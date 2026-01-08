"""Property and RoomType Pydantic schemas."""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class RoomTypeCreate(BaseModel):
    """Schema for creating a room type."""
    name: str
    base_occupancy: int = 2
    max_occupancy: int = 4
    total_rooms: int = 1


class RoomTypeResponse(BaseModel):
    """Schema for room type response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    property_id: int
    name: str
    base_occupancy: int
    max_occupancy: int
    total_rooms: int
    created_at: datetime


class PropertyCreate(BaseModel):
    """Schema for creating a property."""
    name: str
    address: Optional[str] = None
    timezone: str = "UTC"
    room_types: Optional[List[RoomTypeCreate]] = None


class PropertyResponse(BaseModel):
    """Schema for property response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    address: Optional[str]
    timezone: str
    created_at: datetime
    updated_at: datetime
    room_types: List[RoomTypeResponse] = []
