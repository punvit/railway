"""Redis-based distributed lock manager for preventing race conditions."""

import asyncio
from datetime import date
from typing import Optional
import redis.asyncio as redis

from app.config import get_settings

settings = get_settings()


class LockManager:
    """Distributed lock manager using Redis for inventory operations."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize lock manager with optional Redis client."""
        self._redis: Optional[redis.Redis] = redis_client
        self._lock_prefix = "inventory_lock"
    
    async def get_redis(self) -> redis.Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis
    
    def _get_lock_key(self, room_type_id: int, lock_date: date) -> str:
        """Generate unique lock key for room type and date."""
        return f"{self._lock_prefix}:{room_type_id}:{lock_date.isoformat()}"
    
    async def acquire_lock(
        self,
        room_type_id: int,
        lock_date: date,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """
        Attempt to acquire a distributed lock for a specific room type and date.
        
        Args:
            room_type_id: The room type ID to lock
            lock_date: The specific date to lock inventory for
            ttl_seconds: Lock time-to-live in seconds (default from settings)
            
        Returns:
            True if lock was acquired, False otherwise
        """
        redis_client = await self.get_redis()
        lock_key = self._get_lock_key(room_type_id, lock_date)
        ttl = ttl_seconds or settings.lock_ttl_seconds
        
        # Use SET NX (only set if not exists) with expiry
        acquired = await redis_client.set(
            lock_key,
            "locked",
            nx=True,  # Only set if not exists
            ex=ttl,   # Expiry in seconds
        )
        return bool(acquired)
    
    async def release_lock(self, room_type_id: int, lock_date: date) -> bool:
        """
        Release a distributed lock.
        
        Args:
            room_type_id: The room type ID
            lock_date: The date to unlock
            
        Returns:
            True if lock was released, False if lock didn't exist
        """
        redis_client = await self.get_redis()
        lock_key = self._get_lock_key(room_type_id, lock_date)
        deleted = await redis_client.delete(lock_key)
        return bool(deleted)
    
    async def acquire_lock_with_retry(
        self,
        room_type_id: int,
        lock_date: date,
        max_attempts: Optional[int] = None,
        retry_delay_ms: Optional[int] = None,
    ) -> bool:
        """
        Attempt to acquire lock with retries.
        
        Args:
            room_type_id: The room type ID to lock
            lock_date: The specific date to lock
            max_attempts: Maximum number of acquisition attempts
            retry_delay_ms: Delay between retries in milliseconds
            
        Returns:
            True if lock was acquired, False after all retries failed
        """
        attempts = max_attempts or settings.lock_retry_attempts
        delay = (retry_delay_ms or settings.lock_retry_delay_ms) / 1000.0
        
        for attempt in range(attempts):
            if await self.acquire_lock(room_type_id, lock_date):
                return True
            if attempt < attempts - 1:
                await asyncio.sleep(delay)
        
        return False
    
    async def acquire_multi_date_lock(
        self,
        room_type_id: int,
        dates: list[date],
    ) -> bool:
        """
        Acquire locks for multiple dates atomically.
        If any lock fails, releases all previously acquired locks.
        
        Args:
            room_type_id: The room type ID to lock
            dates: List of dates to lock
            
        Returns:
            True if all locks were acquired, False otherwise
        """
        acquired_dates: list[date] = []
        
        for lock_date in sorted(dates):
            if await self.acquire_lock(room_type_id, lock_date):
                acquired_dates.append(lock_date)
            else:
                # Rollback: release all acquired locks
                for acquired in acquired_dates:
                    await self.release_lock(room_type_id, acquired)
                return False
        
        return True
    
    async def release_multi_date_lock(
        self,
        room_type_id: int,
        dates: list[date],
    ) -> None:
        """Release locks for multiple dates."""
        for lock_date in dates:
            await self.release_lock(room_type_id, lock_date)
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None


# Global lock manager instance
_lock_manager: Optional[LockManager] = None


def get_lock_manager() -> LockManager:
    """Get global lock manager instance."""
    global _lock_manager
    if _lock_manager is None:
        _lock_manager = LockManager()
    return _lock_manager
