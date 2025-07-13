"""
API endpoints for channel management
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import asyncio
import uuid
import csv
from io import StringIO

from app.config.database import get_db
from app.models.models import AcestreamChannel, TVChannel
from app.services.acestreamchannel_service import AcestreamChannelService
from app.services.channel_status_service import ChannelStatusService
from app.schemas.channel import ChannelResponse, TVChannelResponse, ChannelCreate, ChannelUpdate, TVChannelCreate, TVChannelUpdate
from app.schemas.channel_status import ChannelStatusResponse, BulkStatusCheckResponse, ChannelStatusSummary, StatusCheckRequest
from app.schemas.channel import ChannelListResponse

router = APIRouter()


@router.get("/", response_model=ChannelListResponse)
async def get_channels(
    skip: int = Query(0, alias="skip"),
    limit: int = Query(100, alias="limit"),
    page: int = Query(None, alias="page"),
    page_size: int = Query(None, alias="page_size"),
    active_only: Optional[bool] = None,  # Changed default to None
    search: Optional[str] = None,
    group: Optional[str] = None,
    country: Optional[str] = None,
    language: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_online: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Get all channels with optional filtering.
    Supports both skip/limit and page/page_size parameters.
    Returns paginated items and total count.
    """
    # Convert page/page_size to skip/limit if provided
    if page is not None and page_size is not None:
        skip = (page - 1) * page_size
        limit = page_size

    if is_active is not None:
        active_only = False
    if active_only is None:
        active_only = False

    service = AcestreamChannelService(db)
    items, total = service.get_advanced_filtered_channels_with_total(
        skip=skip,
        limit=limit,
        active_only=active_only,
        search=search,
        group=group,
        country=country,
        language=language,
        is_active=is_active,
        is_online=is_online
    )
    return {"items": items, "total": total}


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
    service = AcestreamChannelService(db)
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
    service = AcestreamChannelService(db)
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
        # Return all required fields for BulkStatusCheckResponse (with defaults)
        return {
            "message": f"Status check started in background for {len(channels)} channels. This will finish when it finishes.",
            "background": True,
            "total_channels": len(channels),
            "total_checked": 0,
            "online_count": 0,
            "offline_count": 0,
            "results": [],
            "summary": status_service.get_channel_status_summary()
        }
    else:
        # Check immediately for small numbers
        results = await status_service.check_multiple_channels(channels, concurrency)
        summary = status_service.get_channel_status_summary()

        # Count online and offline channels
        online_count = sum(1 for r in results if r["is_online"])
        offline_count = sum(1 for r in results if not r["is_online"])

        return {
            "message": f"Status check completed for {len(channels)} channels.",
            "background": False,
            "total_channels": len(channels),
            "total_checked": len(results),
            "online_count": online_count,
            "offline_count": offline_count,
            "results": results,
            "summary": summary
        }


@router.get("/tv/", response_model=List[TVChannelResponse])
async def get_tv_channels(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all TV channels.
    """
    service = AcestreamChannelService(db)
    return service.get_all_tv_channels(skip=skip, limit=limit)


@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(channel_id: str, db: Session = Depends(get_db)):
    """
    Get a specific channel by ID.
    """
    service = AcestreamChannelService(db)
    channel = service.get_channel_by_id(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel


@router.post("/{channel_id}/check_status", response_model=ChannelStatusResponse)
async def check_channel_status(channel_id: str, db: Session = Depends(get_db)):
    """
    Check the online status of a specific channel via Acestream engine.
    """
    service = AcestreamChannelService(db)
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
    service = AcestreamChannelService(db)
    channel_id = channel.id or str(uuid.uuid4())
    existing_channel = service.get_channel_by_id(channel_id)

    if existing_channel:
        # Update existing channel (upsert behavior for V1 compatibility)
        updated_channel = service.update_channel(
            channel_id=channel_id,
            updates=channel.model_dump(exclude_unset=True)
        )
        return updated_channel
    else:
        # Create new channel
        return service.create_channel(
            channel_id=channel_id,
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
    service = AcestreamChannelService(db)
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
    service = AcestreamChannelService(db)
    existing_channel = service.get_channel_by_id(channel_id)
    if not existing_channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    service.delete_channel(channel_id)
    return None


@router.post("/bulk_delete", status_code=status.HTTP_204_NO_CONTENT)
async def bulk_delete_channels(
    channel_ids: List[str] = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """
    Delete multiple channels by IDs.
    """
    service = AcestreamChannelService(db)
    deleted = service.bulk_delete_channels(channel_ids)
    if not deleted:
        raise HTTPException(status_code=404, detail="No channels deleted")
    return None


@router.put("/bulk_edit", response_model=List[ChannelResponse])
async def bulk_edit_channels(
    updates: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Update multiple channels by IDs and fields.
    updates: {"channel_ids": [...], "fields": {...}}
    """
    service = AcestreamChannelService(db)
    channel_ids = updates.get("channel_ids", [])
    fields = updates.get("fields", {})
    if not channel_ids or not fields:
        raise HTTPException(status_code=400, detail="channel_ids and fields required")
    updated = service.bulk_update_channels(channel_ids, fields)
    return updated


@router.post("/bulk_activate", response_model=List[ChannelResponse])
async def bulk_activate_channels(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Activate/deactivate multiple channels by IDs.
    data: {"channel_ids": [...], "active": true/false}
    """
    service = AcestreamChannelService(db)
    channel_ids = data.get("channel_ids", [])
    active = data.get("active", True)
    if not channel_ids:
        raise HTTPException(status_code=400, detail="channel_ids required")
    updated = service.bulk_activate_channels(channel_ids, active)
    return updated


@router.get("/export_csv")
def export_channels_csv(db: Session = Depends(get_db)):
    """
    Export all channels as a CSV file.
    """
    service = AcestreamChannelService(db)
    channels = service.get_all_channels(active_only=False)
    output = StringIO()
    writer = csv.writer(output)
    # Write header
    writer.writerow([
        "id", "name", "source_url", "group", "logo", "tvg_id", "tvg_name", "is_online", "is_active", "last_seen"
    ])
    for ch in channels:
        writer.writerow([
            ch.id, ch.name, ch.source_url, ch.group, ch.logo, ch.tvg_id, ch.tvg_name, ch.is_online, getattr(ch, 'is_active', ''), getattr(ch, 'last_seen', '')
        ])
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=channels.csv"})


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

