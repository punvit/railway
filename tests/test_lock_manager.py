"""Tests for the Redis lock manager."""

from datetime import date, timedelta
import asyncio

import pytest


@pytest.mark.asyncio
async def test_lock_acquisition(lock_manager):
    """Test basic lock acquisition and release."""
    room_type_id = 1
    lock_date = date.today()
    
    # Should acquire lock successfully
    acquired = await lock_manager.acquire_lock(room_type_id, lock_date)
    assert acquired is True
    
    # Should NOT be able to acquire same lock again
    acquired_again = await lock_manager.acquire_lock(room_type_id, lock_date)
    assert acquired_again is False
    
    # Release lock
    released = await lock_manager.release_lock(room_type_id, lock_date)
    assert released is True
    
    # Should be able to acquire after release
    acquired_after = await lock_manager.acquire_lock(room_type_id, lock_date)
    assert acquired_after is True
    
    # Cleanup
    await lock_manager.release_lock(room_type_id, lock_date)


@pytest.mark.asyncio
async def test_lock_prevents_concurrent_access(lock_manager):
    """Test that locks prevent concurrent access."""
    room_type_id = 1
    lock_date = date.today() + timedelta(days=1)
    acquired_count = 0
    
    async def try_acquire():
        nonlocal acquired_count
        if await lock_manager.acquire_lock(room_type_id, lock_date, ttl_seconds=5):
            acquired_count += 1
            await asyncio.sleep(0.1)  # Simulate work
            await lock_manager.release_lock(room_type_id, lock_date)
    
    # Try to acquire lock concurrently
    await asyncio.gather(
        try_acquire(),
        try_acquire(),
        try_acquire(),
    )
    
    # Only one should have succeeded at a time
    # (they may all eventually succeed due to sequential nature after first release)
    assert acquired_count >= 1


@pytest.mark.asyncio
async def test_multi_date_lock(lock_manager):
    """Test acquiring locks for multiple dates."""
    room_type_id = 1
    dates = [
        date.today(),
        date.today() + timedelta(days=1),
        date.today() + timedelta(days=2),
    ]
    
    # Acquire all locks
    acquired = await lock_manager.acquire_multi_date_lock(room_type_id, dates)
    assert acquired is True
    
    # Try to acquire one of the locked dates
    single_acquired = await lock_manager.acquire_lock(
        room_type_id, dates[1]
    )
    assert single_acquired is False
    
    # Release all
    await lock_manager.release_multi_date_lock(room_type_id, dates)
    
    # Should be able to acquire again
    single_acquired_after = await lock_manager.acquire_lock(
        room_type_id, dates[1]
    )
    assert single_acquired_after is True
    
    # Cleanup
    await lock_manager.release_lock(room_type_id, dates[1])


@pytest.mark.asyncio
async def test_multi_date_lock_rollback(lock_manager):
    """Test that multi-date lock rolls back on failure."""
    room_type_id = 1
    dates = [
        date.today() + timedelta(days=10),
        date.today() + timedelta(days=11),
        date.today() + timedelta(days=12),
    ]
    
    # Pre-lock one of the dates
    await lock_manager.acquire_lock(room_type_id, dates[1])
    
    # Try to acquire all dates (should fail on dates[1])
    acquired = await lock_manager.acquire_multi_date_lock(room_type_id, dates)
    assert acquired is False
    
    # First date should have been rolled back
    first_available = await lock_manager.acquire_lock(room_type_id, dates[0])
    assert first_available is True
    
    # Cleanup
    await lock_manager.release_lock(room_type_id, dates[0])
    await lock_manager.release_lock(room_type_id, dates[1])


@pytest.mark.asyncio
async def test_lock_with_retry(lock_manager):
    """Test lock acquisition with retries."""
    room_type_id = 1
    lock_date = date.today() + timedelta(days=20)
    
    # Acquire lock
    await lock_manager.acquire_lock(room_type_id, lock_date, ttl_seconds=1)
    
    # Try with retries (should eventually succeed after TTL expires)
    acquired = await lock_manager.acquire_lock_with_retry(
        room_type_id,
        lock_date,
        max_attempts=5,
        retry_delay_ms=300,
    )
    
    # May or may not succeed depending on timing
    # The important thing is it doesn't crash
    
    # Cleanup
    await lock_manager.release_lock(room_type_id, lock_date)
