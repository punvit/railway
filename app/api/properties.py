"""Property and room type management endpoints."""

from typing import List
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.property import Property, RoomType
from app.models.channel import ChannelMapping
from app.schemas.property import (
    PropertyCreate,
    PropertyResponse,
    RoomTypeCreate,
    RoomTypeResponse,
)
from app.schemas.channel import ChannelMappingCreate, ChannelMappingResponse
from app.services.sync_engine import initialize_inventory

router = APIRouter()


@router.post(
    "/",
    response_model=PropertyResponse,
    status_code=201,
    summary="Create a new property",
)
async def create_property(
    property_data: PropertyCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new hotel property with optional room types.
    """
    property_obj = Property(
        name=property_data.name,
        address=property_data.address,
        timezone=property_data.timezone,
    )
    db.add(property_obj)
    await db.flush()
    
    # Add room types if provided
    if property_data.room_types:
        for rt_data in property_data.room_types:
            room_type = RoomType(
                property_id=property_obj.id,
                name=rt_data.name,
                base_occupancy=rt_data.base_occupancy,
                max_occupancy=rt_data.max_occupancy,
                total_rooms=rt_data.total_rooms,
            )
            db.add(room_type)
    
    await db.flush()
    await db.refresh(property_obj)
    
    # Reload with relationships
    result = await db.execute(
        select(Property)
        .options(selectinload(Property.room_types))
        .where(Property.id == property_obj.id)
    )
    property_obj = result.scalar_one()
    
    return PropertyResponse.model_validate(property_obj)


@router.get(
    "/",
    response_model=List[PropertyResponse],
    summary="List all properties",
)
async def list_properties(
    db: AsyncSession = Depends(get_db),
):
    """Get all properties with their room types."""
    result = await db.execute(
        select(Property).options(selectinload(Property.room_types))
    )
    properties = result.scalars().all()
    return [PropertyResponse.model_validate(p) for p in properties]


@router.get(
    "/{property_id}",
    response_model=PropertyResponse,
    summary="Get property by ID",
)
async def get_property(
    property_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific property with its room types."""
    result = await db.execute(
        select(Property)
        .options(selectinload(Property.room_types))
        .where(Property.id == property_id)
    )
    property_obj = result.scalar_one_or_none()
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    return PropertyResponse.model_validate(property_obj)


@router.post(
    "/{property_id}/room-types",
    response_model=RoomTypeResponse,
    status_code=201,
    summary="Add room type to property",
)
async def add_room_type(
    property_id: int,
    room_type_data: RoomTypeCreate,
    initialize: bool = Query(False, description="Initialize 365 days of inventory"),
    default_price: Decimal = Query(Decimal("100.00"), description="Default price if initializing"),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a new room type to an existing property.
    
    Optionally initialize inventory for 365 days.
    """
    # Verify property exists
    prop_result = await db.execute(
        select(Property).where(Property.id == property_id)
    )
    if not prop_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Property not found")
    
    room_type = RoomType(
        property_id=property_id,
        name=room_type_data.name,
        base_occupancy=room_type_data.base_occupancy,
        max_occupancy=room_type_data.max_occupancy,
        total_rooms=room_type_data.total_rooms,
    )
    db.add(room_type)
    await db.flush()
    await db.refresh(room_type)
    
    # Initialize inventory if requested
    if initialize:
        await initialize_inventory(
            db=db,
            room_type_id=room_type.id,
            total_rooms=room_type.total_rooms,
            base_price=default_price,
            days=365,
        )
    
    return RoomTypeResponse.model_validate(room_type)


@router.post(
    "/room-types/{room_type_id}/channel-mapping",
    response_model=ChannelMappingResponse,
    status_code=201,
    summary="Create channel mapping",
)
async def create_channel_mapping(
    room_type_id: int,
    mapping_data: ChannelMappingCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Map a local room type to an OTA room ID.
    
    This enables synchronization with the specified OTA channel.
    """
    # Verify room type exists
    rt_result = await db.execute(
        select(RoomType).where(RoomType.id == room_type_id)
    )
    if not rt_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Room type not found")
    
    mapping = ChannelMapping(
        room_type_id=room_type_id,
        channel_name=mapping_data.channel_name,
        ota_room_id=mapping_data.ota_room_id,
        ota_property_id=mapping_data.ota_property_id,
        is_active=mapping_data.is_active,
        ical_url=mapping_data.ical_url,
    )
    db.add(mapping)
    await db.flush()
    await db.refresh(mapping)
    
    return ChannelMappingResponse.model_validate(mapping)


@router.get(
    "/room-types/{room_type_id}/channel-mappings",
    response_model=List[ChannelMappingResponse],
    summary="List channel mappings",
)
async def list_channel_mappings(
    room_type_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all channel mappings for a room type."""
    result = await db.execute(
        select(ChannelMapping).where(ChannelMapping.room_type_id == room_type_id)
    )
    mappings = result.scalars().all()
    return [ChannelMappingResponse.model_validate(m) for m in mappings]
