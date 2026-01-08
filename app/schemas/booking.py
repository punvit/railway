"""Booking Pydantic schemas."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BookingCreate(BaseModel):
    """Schema for creating a booking (internal)."""
    room_type_id: int
    channel_name: str
    ota_booking_id: str
    check_in: date
    check_out: date
    guest_name: Optional[str] = None
    guest_email: Optional[str] = None
    num_guests: int = 1


class BookingWebhookPayload(BaseModel):
    """Schema for OTA webhook booking payload."""
    channel: str = Field(..., description="OTA channel name (booking_com, airbnb, etc.)")
    ota_booking_id: str = Field(..., description="Booking ID from the OTA")
    room_type_id: int = Field(..., description="Local room type ID")
    check_in: date
    check_out: date
    guest_name: Optional[str] = None
    guest_email: Optional[str] = None
    num_guests: int = 1


class BookingResponse(BaseModel):
    """Schema for booking response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    room_type_id: int
    channel_name: str
    ota_booking_id: str
    check_in: date
    check_out: date
    guest_name: Optional[str]
    guest_email: Optional[str]
    num_guests: int
    status: str
    created_at: datetime


class BookingResult(BaseModel):
    """Result of a booking operation."""
    success: bool
    message: str
    booking: Optional[BookingResponse] = None
