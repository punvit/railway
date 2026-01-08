"""Sync engine for managing inventory updates and OTA synchronization."""

import asyncio
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import InventoryLedger
from app.models.booking import Booking, BookingStatus
from app.models.channel import ChannelMapping
from app.schemas.booking import BookingCreate, BookingResponse, BookingResult
from app.services.lock_manager import LockManager, get_lock_manager
from app.services.channel_adapter import get_channel_adapter


class SyncEngine:
    """
    Master sync engine for coordinating inventory updates across channels.
    
    Responsibilities:
    - Atomic inventory updates with distributed locking
    - Availability broadcast to connected OTAs
    - Rate parity management across channels
    """
    
    def __init__(
        self,
        db: AsyncSession,
        lock_manager: Optional[LockManager] = None,
    ):
        """Initialize sync engine."""
        self.db = db
        self.lock_manager = lock_manager or get_lock_manager()
    
    async def process_booking(
        self,
        booking_data: BookingCreate,
    ) -> BookingResult:
        """
        Process an incoming booking with atomic inventory update.
        
        This method:
        1. Acquires distributed locks for all affected dates
        2. Checks availability for each night
        3. Decrements inventory atomically
        4. Creates booking record
        5. Triggers availability broadcast
        
        Args:
            booking_data: Booking details from OTA
            
        Returns:
            BookingResult with success status and booking details
        """
        # Calculate all dates in the booking range
        booking_dates = self._get_date_range(
            booking_data.check_in,
            booking_data.check_out,
        )
        
        if not booking_dates:
            return BookingResult(
                success=False,
                message="Invalid date range: check-out must be after check-in",
            )
        
        # Try to acquire locks for all dates
        locks_acquired = await self.lock_manager.acquire_multi_date_lock(
            booking_data.room_type_id,
            booking_dates,
        )
        
        if not locks_acquired:
            return BookingResult(
                success=False,
                message="Unable to acquire inventory lock. Please retry.",
            )
        
        try:
            # Check availability for all dates
            availability_check = await self._check_availability(
                booking_data.room_type_id,
                booking_dates,
            )
            
            if not availability_check["available"]:
                return BookingResult(
                    success=False,
                    message=f"No availability for dates: {availability_check['unavailable_dates']}",
                )
            
            # Decrement inventory for all dates
            await self._decrement_inventory(
                booking_data.room_type_id,
                booking_dates,
            )
            
            # Create booking record
            booking = Booking(
                room_type_id=booking_data.room_type_id,
                channel_name=booking_data.channel_name,
                ota_booking_id=booking_data.ota_booking_id,
                check_in=booking_data.check_in,
                check_out=booking_data.check_out,
                guest_name=booking_data.guest_name,
                guest_email=booking_data.guest_email,
                num_guests=booking_data.num_guests,
                status=BookingStatus.CONFIRMED.value,
            )
            self.db.add(booking)
            await self.db.flush()
            await self.db.refresh(booking)
            
            # Trigger async availability broadcast (fire and forget)
            asyncio.create_task(
                self.broadcast_availability(
                    booking_data.room_type_id,
                    booking_dates,
                )
            )
            
            return BookingResult(
                success=True,
                message="Booking confirmed successfully",
                booking=BookingResponse.model_validate(booking),
            )
            
        finally:
            # Always release locks
            await self.lock_manager.release_multi_date_lock(
                booking_data.room_type_id,
                booking_dates,
            )
    
    async def _check_availability(
        self,
        room_type_id: int,
        dates: List[date],
    ) -> dict:
        """Check if rooms are available for all specified dates."""
        unavailable_dates = []
        
        for check_date in dates:
            result = await self.db.execute(
                select(InventoryLedger).where(
                    and_(
                        InventoryLedger.room_type_id == room_type_id,
                        InventoryLedger.date == check_date,
                    )
                )
            )
            inventory = result.scalar_one_or_none()
            
            if inventory is None or inventory.available_rooms < 1:
                unavailable_dates.append(check_date.isoformat())
        
        return {
            "available": len(unavailable_dates) == 0,
            "unavailable_dates": unavailable_dates,
        }
    
    async def _decrement_inventory(
        self,
        room_type_id: int,
        dates: List[date],
    ) -> None:
        """Decrement available rooms for specified dates."""
        for decr_date in dates:
            result = await self.db.execute(
                select(InventoryLedger).where(
                    and_(
                        InventoryLedger.room_type_id == room_type_id,
                        InventoryLedger.date == decr_date,
                    )
                )
            )
            inventory = result.scalar_one_or_none()
            
            if inventory and inventory.available_rooms >= 1:
                inventory.available_rooms -= 1
                inventory.version += 1
    
    async def broadcast_availability(
        self,
        room_type_id: int,
        dates: List[date],
    ) -> None:
        """
        Broadcast availability updates to all connected channels.
        
        This is typically called asynchronously after inventory changes.
        """
        # Get all active channel mappings for this room type
        result = await self.db.execute(
            select(ChannelMapping).where(
                and_(
                    ChannelMapping.room_type_id == room_type_id,
                    ChannelMapping.is_active == True,
                )
            )
        )
        mappings = result.scalars().all()
        
        # Get current inventory for affected dates
        inventory_result = await self.db.execute(
            select(InventoryLedger).where(
                and_(
                    InventoryLedger.room_type_id == room_type_id,
                    InventoryLedger.date.in_(dates),
                )
            )
        )
        inventories = {inv.date: inv for inv in inventory_result.scalars().all()}
        
        # Push to each channel
        for mapping in mappings:
            adapter = get_channel_adapter(mapping.channel_name)
            if adapter:
                for inv_date, inventory in inventories.items():
                    await adapter.push_availability(
                        ota_room_id=mapping.ota_room_id,
                        date=inv_date,
                        available_rooms=inventory.available_rooms,
                    )
    
    async def update_rate_parity(
        self,
        room_type_id: int,
        target_date: date,
        new_price: Decimal,
    ) -> dict:
        """
        Push a single price update to all mapped channels simultaneously.
        
        Rate parity ensures all OTAs show the same price.
        
        Args:
            room_type_id: Room type to update
            target_date: Date to update price for
            new_price: New price to set
            
        Returns:
            Dict with update results per channel
        """
        # Update local inventory price
        result = await self.db.execute(
            select(InventoryLedger).where(
                and_(
                    InventoryLedger.room_type_id == room_type_id,
                    InventoryLedger.date == target_date,
                )
            )
        )
        inventory = result.scalar_one_or_none()
        
        if inventory:
            inventory.base_price = new_price
            inventory.version += 1
        
        # Get all active channel mappings
        mapping_result = await self.db.execute(
            select(ChannelMapping).where(
                and_(
                    ChannelMapping.room_type_id == room_type_id,
                    ChannelMapping.is_active == True,
                )
            )
        )
        mappings = mapping_result.scalars().all()
        
        # Push to all channels concurrently
        results = {}
        tasks = []
        
        for mapping in mappings:
            adapter = get_channel_adapter(mapping.channel_name)
            if adapter:
                task = adapter.push_rate(
                    ota_room_id=mapping.ota_room_id,
                    date=target_date,
                    price=new_price,
                )
                tasks.append((mapping.channel_name, task))
        
        # Execute all rate pushes concurrently
        for channel_name, task in tasks:
            try:
                success = await task
                results[channel_name] = {"success": success}
            except Exception as e:
                results[channel_name] = {"success": False, "error": str(e)}
        
        return {
            "room_type_id": room_type_id,
            "date": target_date.isoformat(),
            "new_price": str(new_price),
            "channel_updates": results,
        }
    
    def _get_date_range(self, check_in: date, check_out: date) -> List[date]:
        """Get list of dates from check-in to check-out (exclusive of check-out)."""
        if check_out <= check_in:
            return []
        
        dates = []
        current = check_in
        while current < check_out:
            dates.append(current)
            current += timedelta(days=1)
        
        return dates


async def initialize_inventory(
    db: AsyncSession,
    room_type_id: int,
    total_rooms: int,
    base_price: Decimal,
    days: int = 365,
) -> None:
    """
    Initialize inventory ledger for a room type for the next N days.
    
    Args:
        db: Database session
        room_type_id: Room type to initialize
        total_rooms: Number of rooms available
        base_price: Default price per night
        days: Number of days to initialize (default 365)
    """
    from datetime import date as date_type
    
    today = date_type.today()
    
    for day_offset in range(days):
        inv_date = today + timedelta(days=day_offset)
        
        # Check if entry already exists
        result = await db.execute(
            select(InventoryLedger).where(
                and_(
                    InventoryLedger.room_type_id == room_type_id,
                    InventoryLedger.date == inv_date,
                )
            )
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            inventory = InventoryLedger(
                room_type_id=room_type_id,
                date=inv_date,
                available_rooms=total_rooms,
                base_price=base_price,
            )
            db.add(inventory)
    
    await db.flush()
