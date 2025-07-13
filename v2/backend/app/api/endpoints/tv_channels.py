"""
API endpoints for TV channel management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.config.database import get_db
from app.services.tvchannel_service import TVChannelService
from app.services.acestreamchannel_service import AcestreamChannelService
from app.schemas.channel import TVChannelResponse, TVChannelCreate, TVChannelUpdate, AcestreamChannelResponse

router = APIRouter()


from fastapi import Query

@router.get("/", response_model=Dict[str, Any])
async def get_tv_channels(
    skip: int = Query(0, alias="skip"),
    limit: int = Query(100, alias="limit"),
    page: int = Query(None, alias="page"),
    page_size: int = Query(None, alias="page_size"),
    db: Session = Depends(get_db)
):
    """
    Get all TV channels with pagination and total count.
    """
    # Convert page/page_size to skip/limit if provided
    if page is not None and page_size is not None:
        skip = (page - 1) * page_size
        limit = page_size
    service = TVChannelService(db)
    items, total = service.get_tv_channels_with_total(skip=skip, limit=limit)
    items_serialized = [TVChannelResponse.model_validate(item) for item in items]
    return {"items": items_serialized, "total": total}


@router.get("/{tv_channel_id}", response_model=TVChannelResponse)
async def get_tv_channel(tv_channel_id: int, db: Session = Depends(get_db)):
    """
    Get a specific TV channel by ID.
    """
    service = TVChannelService(db)
    tv_channel = service.get_tv_channel_by_id(tv_channel_id)
    if not tv_channel:
        raise HTTPException(status_code=404, detail="TV Channel not found")
    return tv_channel


@router.post("/", response_model=TVChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_tv_channel(tv_channel: TVChannelCreate, db: Session = Depends(get_db)):
    """
    Create a new TV channel.
    """
    if not tv_channel.name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Name cannot be empty"
        )

    service = TVChannelService(db)
    existing_channel = service.get_tv_channel_by_name(tv_channel.name)
    if existing_channel:
        raise HTTPException(
            status_code=400,
            detail=f"TV Channel with name {tv_channel.name} already exists"
        )

    return service.create_tv_channel(
        name=tv_channel.name,
        logo_url=tv_channel.logo_url,
        description=tv_channel.description,
        category=tv_channel.category,
        country=tv_channel.country,
        language=tv_channel.language,
        website=tv_channel.website,
        epg_id=tv_channel.epg_id,
        epg_source_id=tv_channel.epg_source_id,
        channel_number=tv_channel.channel_number,
        is_active=tv_channel.is_active or True,
        is_favorite=tv_channel.is_favorite or False
    )


@router.put("/{tv_channel_id}", response_model=TVChannelResponse)
async def update_tv_channel(
    tv_channel_id: int,
    tv_channel_update: TVChannelUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing TV channel.
    """
    service = TVChannelService(db)
    existing_channel = service.get_tv_channel_by_id(tv_channel_id)
    if not existing_channel:
        raise HTTPException(status_code=404, detail="TV Channel not found")

    updated_channel = service.update_tv_channel(
        tv_channel_id=tv_channel_id,
        updates=tv_channel_update.dict(exclude_unset=True)
    )
    return updated_channel


@router.delete("/{tv_channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tv_channel(tv_channel_id: int, db: Session = Depends(get_db)):
    """
    Delete a TV channel.
    """
    service = TVChannelService(db)
    existing_channel = service.get_tv_channel_by_id(tv_channel_id)
    if not existing_channel:
        raise HTTPException(status_code=404, detail="TV Channel not found")

    service.delete_tv_channel(tv_channel_id)
    return None


@router.get("/{tv_channel_id}/acestreams", response_model=List[AcestreamChannelResponse])
async def get_tv_channel_acestreams(tv_channel_id: int, db: Session = Depends(get_db)):
    """
    Get all acestream channels associated with a TV channel.
    """
    service = TVChannelService(db)
    tv_channel = service.get_tv_channel_by_id(tv_channel_id)
    if not tv_channel:
        raise HTTPException(status_code=404, detail="TV Channel not found")

    return tv_channel.acestream_channels


@router.post("/{tv_channel_id}/acestreams", status_code=status.HTTP_200_OK)
async def associate_acestream(
    tv_channel_id: int,
    association: dict,
    db: Session = Depends(get_db)
):
    """
    Associate an acestream channel with a TV channel.
    """
    if "acestream_channel_id" not in association:
        raise HTTPException(status_code=422, detail="acestream_channel_id is required")

    acestream_id = association["acestream_channel_id"]
    service = TVChannelService(db)
    success = service.associate_acestream(
        tv_channel_id=tv_channel_id,
        acestream_id=acestream_id
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail="TV Channel or Acestream channel not found"
        )

    return {"message": "Acestream successfully associated with TV channel"}


@router.delete("/{tv_channel_id}/acestreams/{acestream_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_acestream_association(
    tv_channel_id: int,
    acestream_id: str,
    db: Session = Depends(get_db)
):
    """
    Remove association between an acestream channel and a TV channel.
    """
    service = TVChannelService(db)
    success = service.remove_acestream_association(
        tv_channel_id=tv_channel_id,
        acestream_id=acestream_id
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Association between TV channel and Acestream channel not found"
        )

    # Return empty Response with 204 status code
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/batch-assign", status_code=status.HTTP_200_OK)
async def batch_assign_acestreams(
    assignment_data: dict,
    db: Session = Depends(get_db)
):
    """
    Batch assign acestream channels to TV channels.

    The request body should be a dictionary where keys are TV channel IDs
    and values are lists of acestream channel IDs.

    Example:
    {
        "1": ["acestream1", "acestream2"],
        "2": ["acestream3"]
    }
    """
    if "assignments" not in assignment_data:
        raise HTTPException(status_code=422, detail="assignments field is required")

    service = TVChannelService(db)
    results = service.batch_associate_acestreams(assignment_data["assignments"])
    return results


@router.post("/associate-by-epg", status_code=status.HTTP_200_OK)
async def associate_by_epg(db: Session = Depends(get_db)):
    """
    Associate acestream channels with TV channels based on EPG IDs.

    This endpoint attempts to match acestream channels with TV channels
    using EPG IDs and channel names.
    """
    tv_service = TVChannelService(db)
    ace_service = AcestreamChannelService(db)

    # Get all TV channels with EPG IDs
    tv_channels = tv_service.get_all_tv_channels(skip=0, limit=1000)
    tv_channels_with_epg = [tc for tc in tv_channels if tc.epg_id]

    # Get all acestream channels with tvg_id
    acestream_channels = ace_service.get_all_channels(skip=0, limit=10000)
    acestream_channels_with_tvg = [ac for ac in acestream_channels if getattr(ac, 'tvg_id', None)]

    matched_count = 0
    for tv_channel in tv_channels_with_epg:
        for acestream in acestream_channels_with_tvg:
            if tv_channel.epg_id == acestream.tvg_id:
                success = tv_service.associate_acestream(tv_channel.id, acestream.id)
                if success:
                    matched_count += 1
                    break

    return {
        "message": "EPG association completed",
        "matched_count": matched_count,
        "tv_channels_with_epg": len(tv_channels_with_epg),
        "acestreams_with_tvg": len(acestream_channels_with_tvg)
    }


@router.post("/bulk-update-epg", status_code=status.HTTP_200_OK)
async def bulk_update_epg(update_data: dict, db: Session = Depends(get_db)):
    """
    Update EPG IDs for multiple TV channels.

    This endpoint updates EPG IDs for multiple TV channels in a batch.

    Request format:
    {
        "updates": [
            {"tv_channel_id": 1, "epg_id": "new.epg.id1"},
            {"tv_channel_id": 2, "epg_id": "new.epg.id2"}
        ]
    }
    """
    if "updates" not in update_data:
        raise HTTPException(status_code=422, detail="updates field is required")

    updates = update_data["updates"]
    service = TVChannelService(db)

    results = {
        "success_count": 0,
        "failure_count": 0,
        "details": []
    }

    for update in updates:
        if "tv_channel_id" not in update or "epg_id" not in update:
            results["failure_count"] += 1
            results["details"].append({
                "tv_channel_id": update.get("tv_channel_id", "missing"),
                "status": "failure",
                "reason": "Missing required fields"
            })
            continue

        tv_channel_id = update["tv_channel_id"]
        epg_id = update["epg_id"]

        try:
            # Get the TV channel
            tv_channel = service.get_tv_channel_by_id(tv_channel_id)
            if not tv_channel:
                results["failure_count"] += 1
                results["details"].append({
                    "tv_channel_id": tv_channel_id,
                    "status": "failure",
                    "reason": "TV Channel not found"
                })
                continue

            # Update the EPG ID
            updated_channel = service.update_tv_channel(
                tv_channel_id=tv_channel_id,
                updates={"epg_id": epg_id}
            )

            results["success_count"] += 1
            results["details"].append({
                "tv_channel_id": tv_channel_id,
                "status": "success",
                "old_epg_id": tv_channel.epg_id,
                "new_epg_id": epg_id
            })
        except Exception as e:
            results["failure_count"] += 1
            results["details"].append({
                "tv_channel_id": tv_channel_id,
                "status": "failure",
                "reason": str(e)
            })

    return results
