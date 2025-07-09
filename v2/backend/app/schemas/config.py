from pydantic import BaseModel, Field, HttpUrl
from typing import Dict, Any, Optional

class BaseUrlUpdate(BaseModel):
    """Schema for updating the base URL for Acestream links"""
    base_url: str = Field(..., description="Base URL for Acestream links")

class AceEngineUrlUpdate(BaseModel):
    """Schema for updating the Acestream Engine URL"""
    value: str = Field(..., description="Acestream Engine URL")

class RescrapeIntervalUpdate(BaseModel):
    """Schema for updating the rescrape interval"""
    value: str = Field(..., description="Hours between automatic rescrapes")

class AddPidUpdate(BaseModel):
    """Schema for updating the addpid setting"""
    value: str = Field(..., description="Whether to add PID to Acestream links")

class SettingResponse(BaseModel):
    """Schema for a setting response"""
    key: str = Field(..., description="Setting key")
    value: str = Field(..., description="Setting value")

class SettingsResponse(BaseModel):
    """Schema for all settings response"""
    settings: Dict[str, str] = Field(..., description="All settings")

class StatusResponse(BaseModel):
    """Schema for a status check response"""
    status: str = Field(..., description="Status of the component (online, offline, error, etc.)")
    message: str = Field(..., description="Status message")
    details: Optional[str] = Field(None, description="Additional details")

class HealthResponse(BaseModel):
    """Schema for the health check response"""
    status: str = Field(..., description="Overall system status (healthy, degraded, unhealthy)")
    acestream: StatusResponse = Field(..., description="Acestream Engine status")
    database: Dict[str, Any] = Field(..., description="Database connection status")
    settings: Dict[str, Any] = Field(..., description="Application settings")
    version: str = Field(..., description="Application version")
