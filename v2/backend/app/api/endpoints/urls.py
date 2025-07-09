from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.services.url_service import URLService

router = APIRouter()

@router.post("/{url_id}/refresh", status_code=202)
def refresh_url(url_id: int, db: Session = Depends(get_db)):
    """
    Manually refresh a specific URL by ID.
    """
    url_service = URLService(db)
    refreshed = url_service.refresh_url(url_id)
    if not refreshed:
        raise HTTPException(status_code=404, detail="URL not found or refresh failed")
    return {"message": f"Refresh started for URL {url_id}", "success": True}

@router.post("/refresh-all", status_code=202)
def refresh_all_urls(db: Session = Depends(get_db)):
    """
    Manually refresh all URLs.
    """
    url_service = URLService(db)
    count = url_service.refresh_all_urls()
    return {"message": f"Refresh started for {count} URLs", "success": True, "count": count}
