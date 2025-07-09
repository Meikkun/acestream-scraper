from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.repositories.settings_repository import SettingsRepository
from app.services.config_service import ConfigService
from app.schemas.config import HealthResponse

router = APIRouter(tags=["health"])

def get_config_service(db: Session = Depends(get_db)):
    settings_repo = SettingsRepository(db)
    return ConfigService(settings_repo)

@router.get("/health", response_model=HealthResponse)
async def check_health(config_service: ConfigService = Depends(get_config_service)):
    """Check the overall system health"""
    health = config_service.check_system_health()
    return health

@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get system statistics"""
    from app.models.models import AcestreamChannel
    # Query the actual number of channels
    total_channels = db.query(AcestreamChannel).count()
    stats = {
        "channels": total_channels,  # total channels as integer
        "channels_detail": {
            "total": total_channels,
            "online": 0,  # Optionally implement online count
            "offline": 0,
            "unknown": 0
        },
        "urls": {
            "total": 0,
            "active": 0,
            "error": 0
        },
        "epg": {
            "sources": 0,
            "channels": 0,
            "programs": 0
        }
    }
    return stats
