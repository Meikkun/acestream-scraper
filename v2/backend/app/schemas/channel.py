"""
Pydantic schemas for channel data
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


class ChannelBase(BaseModel):
    """Base model for channel data"""
    id: Optional[str] = None  # GUID string, not integer
    name: str = Field(..., min_length=1)


class ChannelCreate(ChannelBase):
    """Schema for channel creation"""
    source_url: Optional[str] = None
    group: Optional[str] = None
    logo: Optional[str] = None
    tvg_id: Optional[str] = None
    tvg_name: Optional[str] = None
    is_online: Optional[bool] = True  # Default to True


class ChannelUpdate(BaseModel):
    """Schema for channel update"""
    name: Optional[str] = None
    group: Optional[str] = None
    logo: Optional[str] = None
    tvg_id: Optional[str] = None
    tvg_name: Optional[str] = None
    source_url: Optional[str] = None
    is_active: Optional[bool] = None
    is_online: Optional[bool] = None  # Added for test compatibility
    tv_channel_id: Optional[int] = None
    epg_update_protected: Optional[bool] = None


class ChannelResponse(ChannelBase):
    """Schema for channel response"""
    source_url: Optional[str] = None
    group: Optional[str] = None
    logo: Optional[str] = None
    tvg_id: Optional[str] = None
    tvg_name: Optional[str] = None
    last_seen: datetime
    is_active: bool
    is_online: Optional[bool] = None
    last_checked: Optional[datetime] = None
    check_error: Optional[str] = None
    tv_channel_id: Optional[int] = None
    epg_update_protected: Optional[bool] = False

    class Config:
        from_attributes = True


class TVChannelBase(BaseModel):
    """Base model for TV channel data"""
    name: str
    logo_url: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    website: Optional[str] = None
    epg_id: Optional[str] = None
    channel_number: Optional[int] = None


class TVChannelCreate(TVChannelBase):
    """Schema for TV channel creation"""
    is_active: Optional[bool] = True
    is_favorite: Optional[bool] = False
    epg_source_id: Optional[int] = None


class TVChannelUpdate(BaseModel):
    """Schema for TV channel update"""
    name: Optional[str] = None
    logo_url: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    website: Optional[str] = None
    epg_id: Optional[str] = None
    is_active: Optional[bool] = None
    is_favorite: Optional[bool] = None
    channel_number: Optional[int] = None
    epg_source_id: Optional[int] = None


class TVChannelResponse(TVChannelBase):
    """Schema for TV channel response"""
    id: int
    epg_source_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool
    is_favorite: bool
    acestream_channels: List[ChannelResponse] = []

    class Config:
        from_attributes = True


class ChannelStatusCheck(BaseModel):
    """Schema for channel status check results"""
    total_channels: int
    online_count: int
    offline_count: int
    status_details: Dict[str, Any]


class ChannelListResponse(BaseModel):
    """Schema for paginated channel results"""
    items: List[ChannelResponse]
    total: int
