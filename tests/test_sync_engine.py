"""Tests for the sync engine."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models.inventory import InventoryLedger
from app.models.booking import Booking
from app.schemas.booking import BookingCreate
from app.services.sync_engine import SyncEngine


@pytest.mark.asyncio
async def test_booking_decrements_inventory(
    db_session,
    sample_property,
    sample_inventory,
    lock_manager,
):
    """Test that processing a booking decrements inventory."""
    room_type = sample_property.room_types[0]
    tomorrow = date.today() + timedelta(days=1)
    day_after = date.today() + timedelta(days=2)
    
    # Get initial inventory count
    result = await db_session.execute(
        select(InventoryLedger).where(
            InventoryLedger.room_type_id == room_type.id,
            InventoryLedger.date == tomorrow,
        )
    )
    initial_inv = result.scalar_one()
    initial_count = initial_inv.available_rooms
    
    # Create booking
    booking_data = BookingCreate(
        room_type_id=room_type.id,
        channel_name="booking_com",
        ota_booking_id="BK_TEST_001",
        check_in=tomorrow,
        check_out=day_after,
        guest_name="Test Guest",
        num_guests=2,
    )
    
    sync_engine = SyncEngine(db_session, lock_manager)
    result = await sync_engine.process_booking(booking_data)
    
    # Verify booking succeeded
    assert result.success is True
    assert result.booking is not None
    assert result.booking.ota_booking_id == "BK_TEST_001"
    
    # Verify inventory was decremented
    await db_session.refresh(initial_inv)
    assert initial_inv.available_rooms == initial_count - 1


@pytest.mark.asyncio
async def test_booking_fails_when_no_availability(
    db_session,
    sample_property,
    lock_manager,
):
    """Test that booking fails when no rooms available."""
    room_type = sample_property.room_types[0]
    tomorrow = date.today() + timedelta(days=1)
    day_after = date.today() + timedelta(days=2)
    
    # Create inventory with 0 rooms
    inv = InventoryLedger(
        room_type_id=room_type.id,
        date=tomorrow,
        available_rooms=0,  # No availability
        base_price=Decimal("100.00"),
    )
    db_session.add(inv)
    await db_session.flush()
    
    booking_data = BookingCreate(
        room_type_id=room_type.id,
        channel_name="booking_com",
        ota_booking_id="BK_FAIL_001",
        check_in=tomorrow,
        check_out=day_after,
        guest_name="Test Guest",
    )
    
    sync_engine = SyncEngine(db_session, lock_manager)
    result = await sync_engine.process_booking(booking_data)
    
    # Verify booking failed
    assert result.success is False
    assert "No availability" in result.message


@pytest.mark.asyncio
async def test_invalid_date_range(db_session, sample_property, lock_manager):
    """Test that invalid date range is rejected."""
    room_type = sample_property.room_types[0]
    tomorrow = date.today() + timedelta(days=1)
    
    # Check-out before check-in
    booking_data = BookingCreate(
        room_type_id=room_type.id,
        channel_name="booking_com",
        ota_booking_id="BK_INVALID_001",
        check_in=tomorrow,
        check_out=tomorrow,  # Same day = invalid
        guest_name="Test Guest",
    )
    
    sync_engine = SyncEngine(db_session, lock_manager)
    result = await sync_engine.process_booking(booking_data)
    
    assert result.success is False
    assert "Invalid date range" in result.message


@pytest.mark.asyncio
async def test_multi_night_booking(
    db_session,
    sample_property,
    sample_inventory,
    lock_manager,
):
    """Test that multi-night booking decrements all nights."""
    room_type = sample_property.room_types[0]
    check_in = date.today()
    check_out = date.today() + timedelta(days=3)  # 3 nights
    
    booking_data = BookingCreate(
        room_type_id=room_type.id,
        channel_name="airbnb",
        ota_booking_id="AB_MULTI_001",
        check_in=check_in,
        check_out=check_out,
        guest_name="Multi Night Guest",
    )
    
    sync_engine = SyncEngine(db_session, lock_manager)
    result = await sync_engine.process_booking(booking_data)
    
    assert result.success is True
    
    # Verify all 3 nights were decremented
    for i in range(3):
        inv_date = check_in + timedelta(days=i)
        inv_result = await db_session.execute(
            select(InventoryLedger).where(
                InventoryLedger.room_type_id == room_type.id,
                InventoryLedger.date == inv_date,
            )
        )
        inv = inv_result.scalar_one()
        # Initial was 5, should now be 4
        assert inv.available_rooms == 4
