"""Mock channel adapters for OTA integrations."""

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BaseChannelAdapter(ABC):
    """Base class for OTA channel adapters."""
    
    @abstractmethod
    async def push_availability(
        self,
        ota_room_id: str,
        date: date,
        available_rooms: int,
    ) -> bool:
        """Push availability update to OTA."""
        pass
    
    @abstractmethod
    async def push_rate(
        self,
        ota_room_id: str,
        date: date,
        price: Decimal,
    ) -> bool:
        """Push rate update to OTA."""
        pass


class BookingComAdapter(BaseChannelAdapter):
    """Mock adapter for Booking.com API."""
    
    async def push_availability(
        self,
        ota_room_id: str,
        date: date,
        available_rooms: int,
    ) -> bool:
        """Push availability to Booking.com (mock)."""
        logger.info(
            f"[Booking.com] Pushing availability: room={ota_room_id}, "
            f"date={date}, available={available_rooms}"
        )
        # In production: make API call to Booking.com
        return True
    
    async def push_rate(
        self,
        ota_room_id: str,
        date: date,
        price: Decimal,
    ) -> bool:
        """Push rate to Booking.com (mock)."""
        logger.info(
            f"[Booking.com] Pushing rate: room={ota_room_id}, "
            f"date={date}, price={price}"
        )
        # In production: make API call to Booking.com
        return True


class AirbnbAdapter(BaseChannelAdapter):
    """Mock adapter for Airbnb API."""
    
    async def push_availability(
        self,
        ota_room_id: str,
        date: date,
        available_rooms: int,
    ) -> bool:
        """Push availability to Airbnb (mock)."""
        logger.info(
            f"[Airbnb] Pushing availability: listing={ota_room_id}, "
            f"date={date}, available={available_rooms}"
        )
        # In production: update Airbnb calendar via API
        return True
    
    async def push_rate(
        self,
        ota_room_id: str,
        date: date,
        price: Decimal,
    ) -> bool:
        """Push rate to Airbnb (mock)."""
        logger.info(
            f"[Airbnb] Pushing rate: listing={ota_room_id}, "
            f"date={date}, price={price}"
        )
        # In production: update Airbnb pricing via API
        return True


class ExpediaAdapter(BaseChannelAdapter):
    """Mock adapter for Expedia API."""
    
    async def push_availability(
        self,
        ota_room_id: str,
        date: date,
        available_rooms: int,
    ) -> bool:
        """Push availability to Expedia (mock)."""
        logger.info(
            f"[Expedia] Pushing availability: room={ota_room_id}, "
            f"date={date}, available={available_rooms}"
        )
        return True
    
    async def push_rate(
        self,
        ota_room_id: str,
        date: date,
        price: Decimal,
    ) -> bool:
        """Push rate to Expedia (mock)."""
        logger.info(
            f"[Expedia] Pushing rate: room={ota_room_id}, "
            f"date={date}, price={price}"
        )
        return True


# Channel adapter registry
_adapters: Dict[str, BaseChannelAdapter] = {
    "booking_com": BookingComAdapter(),
    "airbnb": AirbnbAdapter(),
    "expedia": ExpediaAdapter(),
}


def get_channel_adapter(channel_name: str) -> Optional[BaseChannelAdapter]:
    """Get adapter for specified channel."""
    return _adapters.get(channel_name)


def register_adapter(channel_name: str, adapter: BaseChannelAdapter) -> None:
    """Register a new channel adapter."""
    _adapters[channel_name] = adapter
