"""
Race Condition Test Suite

This module tests the critical race condition scenario where two guests
attempt to book the last available room simultaneously from different
OTA channels (e.g., Booking.com and Airbnb).

The test verifies that the Redis-based distributed lock prevents overbooking.
"""

import asyncio
from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models.inventory import InventoryLedger
from app.models.booking import Booking
from app.schemas.booking import BookingCreate
from app.services.sync_engine import SyncEngine


@pytest.mark.asyncio
async def test_concurrent_booking_last_room(
    db_session,
    sample_property,
    last_room_inventory,
    lock_manager,
):
    """
    CRITICAL TEST: Simulate two channels booking the last room simultaneously.
    
    Scenario:
    - Room type has exactly 1 room available for tomorrow
    - Booking.com and Airbnb both try to book at the same time
    - Expected: Only ONE booking should succeed, the other should fail
    
    This test verifies the Redis lock prevents race condition overbookings.
    """
    room_type = sample_property.room_types[0]
    check_in = last_room_inventory.date
    check_out = check_in + timedelta(days=1)
    
    # Track results
    results = []
    
    async def make_booking(channel: str, booking_id: str):
        """Simulate a booking from specific channel."""
        booking_data = BookingCreate(
            room_type_id=room_type.id,
            channel_name=channel,
            ota_booking_id=booking_id,
            check_in=check_in,
            check_out=check_out,
            guest_name=f"Guest from {channel}",
            num_guests=2,
        )
        
        sync_engine = SyncEngine(db_session, lock_manager)
        result = await sync_engine.process_booking(booking_data)
        results.append({
            "channel": channel,
            "booking_id": booking_id,
            "success": result.success,
            "message": result.message,
        })
        return result
    
    # Execute both bookings concurrently
    await asyncio.gather(
        make_booking("booking_com", "BC_RACE_001"),
        make_booking("airbnb", "AB_RACE_001"),
        return_exceptions=True,
    )
    
    # Analyze results
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    # CRITICAL ASSERTION: Exactly one booking should succeed
    assert len(successful) == 1, (
        f"Expected exactly 1 successful booking, got {len(successful)}. "
        f"Results: {results}"
    )
    
    # The other booking should have failed due to no availability
    assert len(failed) == 1, (
        f"Expected exactly 1 failed booking, got {len(failed)}. "
        f"Results: {results}"
    )
    
    # Failed booking should mention availability issue
    failed_result = failed[0]
    assert "availability" in failed_result["message"].lower() or \
           "lock" in failed_result["message"].lower(), (
        f"Expected availability or lock error, got: {failed_result['message']}"
    )
    
    # Verify final inventory is exactly 0
    await db_session.refresh(last_room_inventory)
    assert last_room_inventory.available_rooms == 0, (
        f"Expected 0 available rooms, got {last_room_inventory.available_rooms}"
    )
    
    # Verify exactly one booking record exists
    booking_result = await db_session.execute(
        select(Booking).where(Booking.room_type_id == room_type.id)
    )
    bookings = booking_result.scalars().all()
    assert len(bookings) == 1, (
        f"Expected exactly 1 booking record, got {len(bookings)}"
    )
    
    print(f"\n✅ Race condition test PASSED!")
    print(f"   Successful booking: {successful[0]['channel']} - {successful[0]['booking_id']}")
    print(f"   Failed booking: {failed[0]['channel']} - {failed[0]['message']}")


@pytest.mark.asyncio
async def test_triple_concurrent_booking(
    db_session,
    sample_property,
    lock_manager,
):
    """
    Test three channels competing for the last room.
    
    Even with 3 concurrent requests, only 1 should succeed.
    """
    room_type = sample_property.room_types[0]
    check_in = date.today() + timedelta(days=5)
    check_out = check_in + timedelta(days=1)
    
    # Create inventory with exactly 1 room
    inv = InventoryLedger(
        room_type_id=room_type.id,
        date=check_in,
        available_rooms=1,
        base_price=Decimal("200.00"),
    )
    db_session.add(inv)
    await db_session.flush()
    
    results = []
    
    async def make_booking(channel: str, booking_id: str):
        booking_data = BookingCreate(
            room_type_id=room_type.id,
            channel_name=channel,
            ota_booking_id=booking_id,
            check_in=check_in,
            check_out=check_out,
            guest_name=f"Guest from {channel}",
        )
        
        sync_engine = SyncEngine(db_session, lock_manager)
        result = await sync_engine.process_booking(booking_data)
        results.append({"channel": channel, "success": result.success})
        return result
    
    # Three concurrent bookings
    await asyncio.gather(
        make_booking("booking_com", "BC_TRIPLE_001"),
        make_booking("airbnb", "AB_TRIPLE_001"),
        make_booking("expedia", "EX_TRIPLE_001"),
        return_exceptions=True,
    )
    
    successful = [r for r in results if r["success"]]
    
    # Exactly one should succeed
    assert len(successful) == 1, (
        f"Expected exactly 1 successful booking from 3 attempts, got {len(successful)}"
    )
    
    print(f"\n✅ Triple concurrent booking test PASSED!")
    print(f"   Winner: {successful[0]['channel']}")


@pytest.mark.asyncio
async def test_sequential_bookings_fill_rooms(
    db_session,
    sample_property,
    lock_manager,
):
    """
    Test that sequential bookings correctly fill all rooms.
    
    With 3 rooms available, 3 sequential bookings should succeed,
    and the 4th should fail.
    """
    room_type = sample_property.room_types[0]
    check_in = date.today() + timedelta(days=10)
    check_out = check_in + timedelta(days=1)
    
    # Create inventory with 3 rooms
    inv = InventoryLedger(
        room_type_id=room_type.id,
        date=check_in,
        available_rooms=3,
        base_price=Decimal("150.00"),
    )
    db_session.add(inv)
    await db_session.flush()
    
    sync_engine = SyncEngine(db_session, lock_manager)
    
    # Make 4 sequential bookings
    for i in range(4):
        booking_data = BookingCreate(
            room_type_id=room_type.id,
            channel_name="booking_com",
            ota_booking_id=f"BC_SEQ_{i:03d}",
            check_in=check_in,
            check_out=check_out,
            guest_name=f"Guest {i+1}",
        )
        
        result = await sync_engine.process_booking(booking_data)
        
        if i < 3:
            # First 3 should succeed
            assert result.success is True, f"Booking {i+1} should succeed"
        else:
            # 4th should fail
            assert result.success is False, "4th booking should fail"
            assert "availability" in result.message.lower()
    
    # Verify final state
    await db_session.refresh(inv)
    assert inv.available_rooms == 0
    
    print("\n✅ Sequential booking test PASSED - all rooms correctly filled")


@pytest.mark.asyncio  
async def test_no_race_condition_with_sufficient_inventory(
    db_session,
    sample_property,
    lock_manager,
):
    """
    Test that with sufficient inventory, multiple concurrent bookings succeed.
    
    This verifies the lock doesn't unnecessarily block valid bookings.
    """
    room_type = sample_property.room_types[0]
    check_in = date.today() + timedelta(days=15)
    check_out = check_in + timedelta(days=1)
    
    # Create inventory with 5 rooms (plenty for 2 bookings)
    inv = InventoryLedger(
        room_type_id=room_type.id,
        date=check_in,
        available_rooms=5,
        base_price=Decimal("100.00"),
    )
    db_session.add(inv)
    await db_session.flush()
    
    async def make_booking(booking_id: str):
        booking_data = BookingCreate(
            room_type_id=room_type.id,
            channel_name="booking_com",
            ota_booking_id=booking_id,
            check_in=check_in,
            check_out=check_out,
            guest_name="Test Guest",
        )
        
        sync_engine = SyncEngine(db_session, lock_manager)
        return await sync_engine.process_booking(booking_data)
    
    # Both bookings should succeed (though one will wait for lock)
    result1, result2 = await asyncio.gather(
        make_booking("BC_PLENTY_001"),
        make_booking("BC_PLENTY_002"),
    )
    
    # Both should succeed when there's plenty of inventory
    # Note: Due to locking, they execute sequentially, but both should pass
    successful_count = sum([result1.success, result2.success])
    assert successful_count == 2, "Both bookings should succeed with sufficient inventory"
    
    await db_session.refresh(inv)
    assert inv.available_rooms == 3  # Started with 5, booked 2
    
    print("\n✅ Sufficient inventory test PASSED - both bookings succeeded")
