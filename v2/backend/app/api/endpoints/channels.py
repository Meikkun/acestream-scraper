"""
API endpoints for channel management
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import asyncio

from app.config.database import get_db
from app.models.models import AcestreamChannel, TVChannel
from app.services.channel_service import ChannelService
from app.services.channel_status_service import ChannelStatusService
from app.schemas.channel import ChannelResponse, TVChannelResponse, ChannelCreate, ChannelUpdate, TVChannelCreate, TVChannelUpdate
from app.schemas.channel_status import ChannelStatusResponse, BulkStatusCheckResponse, ChannelStatusSummary, StatusCheckRequest

router = APIRouter()


@router.get("/", response_model=List[ChannelResponse])
async def get_channels(
    skip: int = Query(0, alias="skip"),
    limit: int = Query(100, alias="limit"),
    page: int = Query(None, alias="page"),
    page_size: int = Query(None, alias="page_size"),
    active_only: bool = True,
    search: Optional[str] = None,
    group: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all channels with optional filtering.
    Supports both skip/limit and page/page_size parameters.
    """
    # Convert page/page_size to skip/limit if provided
    if page is not None and page_size is not None:
        skip = (page - 1) * page_size
        limit = page_size

    service = ChannelService(db)
    if group:
        return service.get_filtered_channels(search=search, group=group)
    return service.get_all_channels(
        skip=skip,
        limit=limit,
        active_only=active_only,
        search=search
    )


@router.get("/status_summary", response_model=ChannelStatusSummary)
async def get_channel_status_summary(db: Session = Depends(get_db)):
    """
    Get summary of channel statuses.
    """
    status_service = ChannelStatusService(db)
    return status_service.get_channel_status_summary()


@router.get("/groups")
async def get_channel_groups(db: Session = Depends(get_db)):
    """
    Get unique channel groups.
    """
    service = ChannelService(db)
    channels = service.get_all_channels(active_only=False)  # Get all channels to extract groups
    groups = list(set(channel.group for channel in channels if channel.group))
    return sorted(groups)


@router.post("/check_status_all", response_model=BulkStatusCheckResponse)
async def check_all_channels_status(
    background_tasks: BackgroundTasks,
    request: Optional[StatusCheckRequest] = None,
    limit: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Check the online status of all active channels or specific channels.
    """
    service = ChannelService(db)
    status_service = ChannelStatusService(db)

    # Get channels to check
    if request and request.channel_ids:
        channels = []
        for channel_id in request.channel_ids:
            channel = service.get_channel_by_id(channel_id)
            if channel:
                channels.append(channel)
    else:
        channels = service.get_all_channels(active_only=True)

    if not channels:
        raise HTTPException(status_code=404, detail="No channels found to check")

    # Apply limit if specified
    if limit:
        channels = channels[:limit]

    # Set concurrency
    concurrency = request.concurrency if request else 3

    # For large numbers of channels, run in background
    if len(channels) > 20:
        # Start background task
        background_tasks.add_task(
            _background_status_check,
            db,
            channels,
            concurrency
        )
        return BulkStatusCheckResponse(
            total_channels=len(channels),
            total_checked=0,
            online_count=0,
            offline_count=0,
            results=[],
            summary=status_service.get_channel_status_summary()
        )
    else:
        # Check immediately for small numbers
        results = await status_service.check_multiple_channels(channels, concurrency)
        summary = status_service.get_channel_status_summary()

        # Count online and offline channels
        online_count = sum(1 for r in results if r["is_online"])
        offline_count = sum(1 for r in results if not r["is_online"])

        return BulkStatusCheckResponse(
            total_channels=len(channels),
            total_checked=len(results),
            online_count=online_count,
            offline_count=offline_count,
            results=results,
            summary=summary
        )


@router.get("/tv/", response_model=List[TVChannelResponse])
async def get_tv_channels(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all TV channels.
    """
    service = ChannelService(db)
    return service.get_all_tv_channels(skip=skip, limit=limit)


@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(channel_id: str, db: Session = Depends(get_db)):
    """
    Get a specific channel by ID.
    """
    service = ChannelService(db)
    channel = service.get_channel_by_id(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel


@router.post("/{channel_id}/check_status", response_model=ChannelStatusResponse)
async def check_channel_status(channel_id: str, db: Session = Depends(get_db)):
    """
    Check the online status of a specific channel via Acestream engine.
    """
    service = ChannelService(db)
    channel = service.get_channel_by_id(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    status_service = ChannelStatusService(db)
    result = await status_service.check_channel_status(channel)
    return result


@router.post("/", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(channel: ChannelCreate, db: Session = Depends(get_db)):
    """
    Create a new Acestream channel. If a channel with the same ID exists, update it.
    """
    service = ChannelService(db)
    existing_channel = service.get_channel_by_id(channel.id)

    if existing_channel:
        # Update existing channel (upsert behavior for V1 compatibility)
        updated_channel = service.update_channel(
            channel_id=channel.id,
            updates=channel.model_dump(exclude_unset=True)
        )
        return updated_channel
    else:
        # Create new channel
        return service.create_channel(
            channel_id=channel.id,
            name=channel.name,
            source_url=channel.source_url,
            group=channel.group,
            logo=channel.logo,
            tvg_id=channel.tvg_id,
            tvg_name=channel.tvg_name,
            is_online=channel.is_online
        )


@router.put("/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    channel_id: str,
    channel_update: ChannelUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing channel.
    """
    service = ChannelService(db)
    existing_channel = service.get_channel_by_id(channel_id)
    if not existing_channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    updated_channel = service.update_channel(
        channel_id=channel_id,
        updates=channel_update.model_dump(exclude_unset=True)
    )
    return updated_channel


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(channel_id: str, db: Session = Depends(get_db)):
    """
    Delete a channel.
    """
    service = ChannelService(db)
    existing_channel = service.get_channel_by_id(channel_id)
    if not existing_channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    service.delete_channel(channel_id)
    return None


@router.post("/{channel_id}/check_status", response_model=ChannelStatusResponse)
async def check_channel_status(channel_id: str, db: Session = Depends(get_db)):
    """
    Check the online status of a specific channel via Acestream engine.
    """
    service = ChannelService(db)
    channel = service.get_channel_by_id(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    status_service = ChannelStatusService(db)
    result = await status_service.check_channel_status(channel)
    return result





async def _background_status_check(
    db: Session,
    channels: List[AcestreamChannel],
    concurrency: int
):
    """Background task for checking channel statuses"""
    try:
        status_service = ChannelStatusService(db)
        await status_service.check_multiple_channels(channels, concurrency)
    except Exception as e:
        # Log error but don't raise (background task)
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Background status check failed: {e}")

