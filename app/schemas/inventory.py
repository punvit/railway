"""Inventory Pydantic schemas."""

from datetime import date
from decimal import Decimal
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class InventoryUpdate(BaseModel):
    """Schema for updating a single inventory entry."""
    date: date
    available_rooms: int = Field(..., ge=0)
    base_price: Decimal = Field(..., ge=0)


class BulkInventoryUpdate(BaseModel):
    """Schema for bulk inventory updates."""
    room_type_id: int
    updates: List[InventoryUpdate]


class InventoryResponse(BaseModel):
    """Schema for inventory response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    room_type_id: int
    date: date
    available_rooms: int
    base_price: Decimal
    version: int


class InventoryQuery(BaseModel):
    """Schema for querying inventory."""
    start_date: date
    end_date: date
