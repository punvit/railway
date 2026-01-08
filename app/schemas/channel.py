"""Channel mapping Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ChannelMappingCreate(BaseModel):
    """Schema for creating a channel mapping."""
    room_type_id: int
    channel_name: str
    ota_room_id: str
    ota_property_id: Optional[str] = None
    is_active: bool = True
    ical_url: Optional[str] = None


class ChannelMappingResponse(BaseModel):
    """Schema for channel mapping response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    room_type_id: int
    channel_name: str
    ota_room_id: str
    ota_property_id: Optional[str]
    is_active: bool
    ical_url: Optional[str]
    created_at: datetime
    updated_at: datetime
