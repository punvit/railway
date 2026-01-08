"""Pydantic schemas package."""

from app.schemas.property import PropertyCreate, PropertyResponse, RoomTypeCreate, RoomTypeResponse
from app.schemas.inventory import InventoryUpdate, InventoryResponse, BulkInventoryUpdate
from app.schemas.booking import BookingCreate, BookingResponse, BookingWebhookPayload
from app.schemas.channel import ChannelMappingCreate, ChannelMappingResponse

__all__ = [
    "PropertyCreate",
    "PropertyResponse",
    "RoomTypeCreate",
    "RoomTypeResponse",
    "InventoryUpdate",
    "InventoryResponse",
    "BulkInventoryUpdate",
    "BookingCreate",
    "BookingResponse",
    "BookingWebhookPayload",
    "ChannelMappingCreate",
    "ChannelMappingResponse",
]
