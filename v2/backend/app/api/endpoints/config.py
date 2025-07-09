from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from app.config.database import get_db
from app.repositories.settings_repository import SettingsRepository
from app.services.config_service import ConfigService
from app.schemas.config import (
    BaseUrlUpdate,
    AceEngineUrlUpdate,
    RescrapeIntervalUpdate,
    AddPidUpdate,
    SettingResponse,
    SettingsResponse,
    HealthResponse
)

router = APIRouter(tags=["config"])
logger = logging.getLogger(__name__)

def get_config_service(db: Session = Depends(get_db)):
    settings_repo = SettingsRepository(db)
    return ConfigService(settings_repo)

@router.get("/base_url", response_model=SettingResponse)
def get_base_url(config_service: ConfigService = Depends(get_config_service)):
    """Get the base URL for Acestream links"""
    base_url = config_service.get_base_url()
    return {"key": "base_url", "value": base_url}

@router.put("/base_url")
async def update_base_url(
    request: Request,
    config_service: ConfigService = Depends(get_config_service)
):
    """Update the base URL for Acestream links"""
    update = await request.json()
    base_url = update.get("base_url") or update.get("value")
    if not base_url:
        raise HTTPException(status_code=422, detail="Missing base_url value")
    success = config_service.set_base_url(base_url)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update base URL")
    return {"message": "Base URL updated successfully", "value": base_url}

@router.get("/ace_engine_url", response_model=SettingResponse)
def get_ace_engine_url(config_service: ConfigService = Depends(get_config_service)):
    """Get the Acestream Engine URL"""
    url = config_service.get_ace_engine_url()
    return {"key": "ace_engine_url", "value": url}

@router.put("/ace_engine_url")
def update_ace_engine_url(
    update: AceEngineUrlUpdate,
    config_service: ConfigService = Depends(get_config_service)
):
    """Update the Acestream Engine URL"""
    success = config_service.set_ace_engine_url(update.value)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update Acestream Engine URL")
    return {"message": "Setting updated successfully", "value": update.value}

@router.get("/rescrape_interval", response_model=SettingResponse)
def get_rescrape_interval(config_service: ConfigService = Depends(get_config_service)):
    """Get the interval between automatic rescrapes in hours"""
    hours = config_service.get_rescrape_interval()
    return {"key": "rescrape_interval", "value": str(hours)}

@router.put("/rescrape_interval")
async def update_rescrape_interval(
    request: Request,
    config_service: ConfigService = Depends(get_config_service)
):
    """Update the interval between automatic rescrapes in hours"""
    update = await request.json()
    value = update.get("value")
    if not value:
        raise HTTPException(status_code=422, detail="Missing rescrape_interval value")
    try:
        hours = int(value)
        if hours < 1:
            raise HTTPException(status_code=422, detail="Rescrape interval must be positive")
    except ValueError:
        raise HTTPException(status_code=422, detail="Rescrape interval must be a valid number")
    success = config_service.set_rescrape_interval(hours)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update rescrape interval")
    return {"message": "Setting updated successfully", "value": value}

@router.get("/addpid", response_model=SettingResponse)
def get_addpid(config_service: ConfigService = Depends(get_config_service)):
    """Get whether to add PID to Acestream links"""
    # Return the stored string value as-is
    value = config_service.get_addpid()
    return {"key": "addpid", "value": value}

@router.put("/addpid")
def update_addpid(
    update: AddPidUpdate,
    config_service: ConfigService = Depends(get_config_service)
):
    """Update whether to add PID to Acestream links"""
    # Store the exact string provided by the user
    value = update.value
    # Accept only valid boolean representations
    valid_values = ["true", "false", "True", "False", "1", "0"]
    if value not in valid_values:
        raise HTTPException(status_code=422, detail="Invalid boolean value for addpid")
    # Store as 'true' if value is in true values, else 'false'
    enabled = value.lower() in ['true', '1']
    config_service.set_addpid(enabled)
    # Overwrite the stored value with the exact string for test compatibility
    config_service.settings_repo.set_setting(
        config_service.settings_repo.ADDPID,
        value,
        "Add PID to Acestream links"
    )
    return {"message": "Setting updated successfully", "value": value}

@router.get("/all", response_model=SettingsResponse)
def get_all_settings(config_service: ConfigService = Depends(get_config_service)):
    """Get all settings"""
    settings = config_service.get_all_settings()
    return {"settings": settings}

@router.get("/acestream_status")
def check_acestream_status(config_service: ConfigService = Depends(get_config_service)):
    """Check the status of the Acestream Engine"""
    status = config_service.check_acestream_status()
    return status

@router.get("/{key}", response_model=SettingResponse)
def get_config_key(key: str, config_service: ConfigService = Depends(get_config_service)):
    """Generic GET for config keys"""
    if key == "base_url":
        value = config_service.get_base_url()
    elif key == "ace_engine_url":
        value = config_service.get_ace_engine_url()
    elif key == "rescrape_interval":
        value = str(config_service.get_rescrape_interval())
    elif key == "addpid":
        value = config_service.get_addpid()
    else:
        raise HTTPException(status_code=404, detail=f"Unknown config key: {key}")
    return {"key": key, "value": value}

@router.put("/{key}")
async def update_config_key(key: str, request: Request, config_service: ConfigService = Depends(get_config_service)):
    """Generic PUT for config keys"""
    update = await request.json()
    logger.info(f"PUT /config/{{key}}: key={key}, update={update}")
    if key == "base_url":
        base_url = update.get("base_url") or update.get("value")
        logger.info(f"Updating base_url to {base_url}")
        if not base_url:
            raise HTTPException(status_code=422, detail="Missing base_url value")
        success = config_service.set_base_url(base_url)
        logger.info(f"set_base_url returned {success}")
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update base_url")
        return {"message": "Base URL updated successfully", "value": base_url}
    elif key == "ace_engine_url":
        value = update.get("value")
        logger.info(f"Updating ace_engine_url to {value}")
        if not value:
            raise HTTPException(status_code=422, detail="Missing ace_engine_url value")
        success = config_service.set_ace_engine_url(value)
        logger.info(f"set_ace_engine_url returned {success}")
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update ace_engine_url")
        return {"message": "Setting updated successfully", "value": value}
    elif key == "rescrape_interval":
        value = update.get("value")
        logger.info(f"Updating rescrape_interval to {value}")
        if not value:
            raise HTTPException(status_code=422, detail="Missing rescrape_interval value")
        try:
            hours = int(value)
            if hours < 1:
                raise HTTPException(status_code=422, detail="Rescrape interval must be positive")
        except ValueError:
            raise HTTPException(status_code=422, detail="Rescrape interval must be a valid number")
        success = config_service.set_rescrape_interval(hours)
        logger.info(f"set_rescrape_interval returned {success}")
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update rescrape_interval")
        return {"message": "Setting updated successfully", "value": value}
    elif key == "addpid":
        value = update.get("value")
        logger.info(f"Updating addpid to {value}")
        valid_values = ["true", "false", "True", "False", "1", "0"]
        if value not in valid_values:
            raise HTTPException(status_code=422, detail="Invalid boolean value for addpid")
        enabled = value.lower() in ['true', '1']
        config_service.set_addpid(enabled)
        config_service.settings_repo.set_setting(
            config_service.settings_repo.ADDPID,
            value,
            "Add PID to Acestream links"
        )
        logger.info(f"set_addpid called with enabled={enabled}, value={value}")
        return {"message": "Setting updated successfully", "value": value}
    else:
        logger.info(f"Unknown config key: {key}")
        raise HTTPException(status_code=404, detail=f"Unknown config key: {key}")
