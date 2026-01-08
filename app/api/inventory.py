"""Inventory management endpoints."""

from datetime import date, timedelta
from typing import List
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.inventory import InventoryLedger
from app.models.property import RoomType
from app.schemas.inventory import InventoryResponse, BulkInventoryUpdate

router = APIRouter()


@router.get(
    "/{room_type_id}",
    response_model=List[InventoryResponse],
    summary="Get inventory for date range",
)
async def get_inventory(
    room_type_id: int,
    start_date: date = Query(..., description="Start date (inclusive)"),
    end_date: date = Query(..., description="End date (inclusive)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get inventory availability for a room type within a date range.
    
    Returns daily availability and pricing information.
    """
    # Validate room type exists
    room_result = await db.execute(
        select(RoomType).where(RoomType.id == room_type_id)
    )
    if not room_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Room type not found")
    
    # Query inventory
    result = await db.execute(
        select(InventoryLedger)
        .where(
            and_(
                InventoryLedger.room_type_id == room_type_id,
                InventoryLedger.date >= start_date,
                InventoryLedger.date <= end_date,
            )
        )
        .order_by(InventoryLedger.date)
    )
    
    inventories = result.scalars().all()
    return [InventoryResponse.model_validate(inv) for inv in inventories]


@router.put(
    "/{room_type_id}",
    response_model=dict,
    summary="Bulk update inventory",
)
async def update_inventory(
    room_type_id: int,
    updates: BulkInventoryUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Bulk update inventory availability and pricing.
    
    Updates or creates inventory entries for specified dates.
    """
    # Validate room type
    room_result = await db.execute(
        select(RoomType).where(RoomType.id == room_type_id)
    )
    room_type = room_result.scalar_one_or_none()
    if not room_type:
        raise HTTPException(status_code=404, detail="Room type not found")
    
    updated_count = 0
    created_count = 0
    
    for update in updates.updates:
        # Check if entry exists
        result = await db.execute(
            select(InventoryLedger).where(
                and_(
                    InventoryLedger.room_type_id == room_type_id,
                    InventoryLedger.date == update.date,
                )
            )
        )
        inventory = result.scalar_one_or_none()
        
        if inventory:
            inventory.available_rooms = update.available_rooms
            inventory.base_price = update.base_price
            inventory.version += 1
            updated_count += 1
        else:
            new_inventory = InventoryLedger(
                room_type_id=room_type_id,
                date=update.date,
                available_rooms=update.available_rooms,
                base_price=update.base_price,
            )
            db.add(new_inventory)
            created_count += 1
    
    await db.flush()
    
    return {
        "success": True,
        "updated": updated_count,
        "created": created_count,
    }


@router.post(
    "/{room_type_id}/initialize",
    response_model=dict,
    summary="Initialize inventory for next 365 days",
)
async def initialize_inventory(
    room_type_id: int,
    available_rooms: int = Query(..., ge=0, description="Number of rooms available"),
    base_price: Decimal = Query(..., ge=0, description="Base price per night"),
    days: int = Query(365, ge=1, le=730, description="Number of days to initialize"),
    db: AsyncSession = Depends(get_db),
):
    """
    Initialize inventory ledger for a room type.
    
    Creates daily inventory entries for the specified number of days
    starting from today.
    """
    from app.services.sync_engine import initialize_inventory as init_inv
    
    # Validate room type
    room_result = await db.execute(
        select(RoomType).where(RoomType.id == room_type_id)
    )
    if not room_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Room type not found")
    
    await init_inv(
        db=db,
        room_type_id=room_type_id,
        total_rooms=available_rooms,
        base_price=base_price,
        days=days,
    )
    
    return {
        "success": True,
        "message": f"Initialized {days} days of inventory for room type {room_type_id}",
    }
