"""Pytest configuration and fixtures."""

import asyncio
from datetime import date, timedelta
from decimal import Decimal
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
import redis.asyncio as redis

from app.database import Base, get_db
from app.models import Property, RoomType, InventoryLedger, ChannelMapping
from app.services.lock_manager import LockManager
from app.main import app


# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Create async engine for tests."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests."""
    async_session_factory = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def redis_client() -> AsyncGenerator[redis.Redis, None]:
    """Create Redis client for tests."""
    client = redis.from_url(
        "redis://localhost:6379/15",  # Use separate DB for tests
        encoding="utf-8",
        decode_responses=True,
    )
    
    # Clear test database
    await client.flushdb()
    
    yield client
    
    # Cleanup
    await client.flushdb()
    await client.close()


@pytest_asyncio.fixture(scope="function")
async def lock_manager(redis_client) -> LockManager:
    """Create lock manager with test Redis."""
    manager = LockManager(redis_client)
    yield manager


@pytest_asyncio.fixture(scope="function")
async def sample_property(db_session: AsyncSession) -> Property:
    """Create a sample property with room type."""
    prop = Property(
        name="Test Hotel",
        address="123 Test Street",
        timezone="UTC",
    )
    db_session.add(prop)
    await db_session.flush()
    
    room_type = RoomType(
        property_id=prop.id,
        name="Deluxe Room",
        base_occupancy=2,
        max_occupancy=4,
        total_rooms=5,
    )
    db_session.add(room_type)
    await db_session.flush()
    
    # Add channel mapping
    mapping = ChannelMapping(
        room_type_id=room_type.id,
        channel_name="booking_com",
        ota_room_id="BCH123456",
        is_active=True,
    )
    db_session.add(mapping)
    await db_session.flush()
    
    await db_session.refresh(prop)
    return prop


@pytest_asyncio.fixture(scope="function")
async def sample_inventory(
    db_session: AsyncSession,
    sample_property: Property,
) -> list[InventoryLedger]:
    """Create sample inventory for next 7 days."""
    room_type = sample_property.room_types[0]
    inventories = []
    
    today = date.today()
    for i in range(7):
        inv = InventoryLedger(
            room_type_id=room_type.id,
            date=today + timedelta(days=i),
            available_rooms=5,
            base_price=Decimal("100.00"),
        )
        db_session.add(inv)
        inventories.append(inv)
    
    await db_session.flush()
    return inventories


@pytest_asyncio.fixture(scope="function")
async def last_room_inventory(
    db_session: AsyncSession,
    sample_property: Property,
) -> InventoryLedger:
    """Create inventory with only 1 room available (for race condition test)."""
    room_type = sample_property.room_types[0]
    
    today = date.today()
    inv = InventoryLedger(
        room_type_id=room_type.id,
        date=today + timedelta(days=1),  # Tomorrow
        available_rooms=1,  # Only 1 room!
        base_price=Decimal("150.00"),
    )
    db_session.add(inv)
    await db_session.flush()
    
    return inv
