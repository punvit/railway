"""Channel mapping model for OTA integration."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.property import RoomType


class ChannelName(str, Enum):
    """Supported OTA channels."""
    BOOKING_COM = "booking_com"
    AIRBNB = "airbnb"
    EXPEDIA = "expedia"
    AGODA = "agoda"
    DIRECT = "direct"


class ChannelMapping(Base):
    """Maps local room types to external OTA room IDs."""
    
    __tablename__ = "channel_mappings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("room_types.id", ondelete="CASCADE"), nullable=False
    )
    channel_name: Mapped[str] = mapped_column(String(50), nullable=False)
    ota_room_id: Mapped[str] = mapped_column(String(255), nullable=False)
    ota_property_id: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ical_url: Mapped[str] = mapped_column(String(500), nullable=True)  # For Airbnb
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    
    # Relationships
    room_type: Mapped["RoomType"] = relationship(
        "RoomType", back_populates="channel_mappings"
    )
    
    def __repr__(self) -> str:
        return (
            f"<ChannelMapping(room_type_id={self.room_type_id}, "
            f"channel={self.channel_name}, ota_room_id='{self.ota_room_id}')>"
        )
