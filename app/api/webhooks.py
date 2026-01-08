"""Webhook endpoints for OTA booking notifications."""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.booking import BookingWebhookPayload, BookingResult
from app.services.sync_engine import SyncEngine
from app.schemas.booking import BookingCreate

router = APIRouter()


@router.post(
    "/booking-received",
    response_model=BookingResult,
    summary="Receive booking notification from OTA",
    description="Endpoint for OTAs to push new booking notifications. "
                "Uses distributed locking to prevent overbooking.",
)
async def receive_booking(
    payload: BookingWebhookPayload,
    db: AsyncSession = Depends(get_db),
):
    """
    Process incoming booking from OTA channel.
    
    This endpoint:
    1. Receives booking data from OTA (Booking.com, Airbnb, etc.)
    2. Acquires distributed lock for affected dates
    3. Checks and decrements inventory atomically
    4. Broadcasts availability update to all channels
    
    Returns success/failure with booking details.
    """
    # Convert webhook payload to internal booking create schema
    booking_data = BookingCreate(
        room_type_id=payload.room_type_id,
        channel_name=payload.channel,
        ota_booking_id=payload.ota_booking_id,
        check_in=payload.check_in,
        check_out=payload.check_out,
        guest_name=payload.guest_name,
        guest_email=payload.guest_email,
        num_guests=payload.num_guests,
    )
    
    # Process booking through sync engine
    sync_engine = SyncEngine(db)
    result = await sync_engine.process_booking(booking_data)
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=result.message,
        )
    
    return result


@router.post(
    "/airbnb/ical-sync",
    summary="Sync Airbnb calendar via iCal",
    description="Trigger iCal synchronization for an Airbnb listing.",
)
async def sync_airbnb_ical(
    room_type_id: int,
    ical_url: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Sync blocked dates from Airbnb iCal feed.
    
    Fetches the iCal calendar and updates local inventory
    to reflect blocked dates.
    """
    from app.services.ical_parser import sync_airbnb_calendar
    
    result = await sync_airbnb_calendar(
        ical_url=ical_url,
        room_type_id=room_type_id,
        db_session=db,
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "iCal sync failed"),
        )
    
    return result
