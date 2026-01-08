"""Rate parity management endpoints."""

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.sync_engine import SyncEngine

router = APIRouter()


@router.post(
    "/{room_type_id}/parity",
    response_model=dict,
    summary="Push rate parity update",
    description="Push a single price update to all mapped OTA channels simultaneously.",
)
async def push_rate_parity(
    room_type_id: int,
    target_date: date = Query(..., description="Date to update rate for"),
    price: Decimal = Query(..., ge=0, description="New price to set"),
    db: AsyncSession = Depends(get_db),
):
    """
    Push rate parity update to all channels.
    
    Updates the local inventory price and broadcasts
    the new rate to all connected OTA channels for the
    specified room type and date.
    
    Rate parity ensures all sales channels reflect the same pricing.
    """
    sync_engine = SyncEngine(db)
    result = await sync_engine.update_rate_parity(
        room_type_id=room_type_id,
        target_date=target_date,
        new_price=price,
    )
    
    return result
