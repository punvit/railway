"""Booking model for reservation tracking."""

from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.property import RoomType


class BookingStatus(str, Enum):
    """Booking status enum."""
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    PENDING = "pending"
    NO_SHOW = "no_show"


class Booking(Base):
    """Reservation/booking model."""
    
    __tablename__ = "bookings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("room_types.id", ondelete="CASCADE"), nullable=False
    )
    channel_name: Mapped[str] = mapped_column(String(50), nullable=False)
    ota_booking_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    check_in: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    check_out: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    guest_name: Mapped[str] = mapped_column(String(255), nullable=True)
    guest_email: Mapped[str] = mapped_column(String(255), nullable=True)
    num_guests: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(
        String(20), default=BookingStatus.CONFIRMED.value, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    
    # Relationships
    room_type: Mapped["RoomType"] = relationship("RoomType", back_populates="bookings")
    
    def __repr__(self) -> str:
        return (
            f"<Booking(id={self.id}, ota_booking_id='{self.ota_booking_id}', "
            f"check_in={self.check_in}, check_out={self.check_out})>"
        )
