"""
Periodic task for refreshing EPG data.
"""
from app.config.database import SessionLocal
from app.services.epg_service import EPGService
import logging

def run_epg_refresh_task():
    db = SessionLocal()
    try:
        service = EPGService(db)
        results = service.refresh_all_sources()
        logging.getLogger("epg_refresh_task").info(f"EPG refresh task completed: {results}")
    except Exception as e:
        logging.getLogger("epg_refresh_task").error(f"EPG refresh task failed: {e}")
    finally:
        db.close()
