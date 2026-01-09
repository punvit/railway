"""Property model for hotel and room management."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey, Numeric, Enum as SQLEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.inventory import InventoryLedger


class RoomType(str, Enum):
    """Room type enum."""
    STANDARD = "standard"
    DELUXE = "deluxe"
    SUITE = "suite"
    TWIN = "twin"


class Property(Base):
    """Hotel property model."""

    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    room_types: Mapped[list["RoomTypeModel"]] = relationship("RoomTypeModel", back_populates="property")


class RoomTypeModel(Base):
    """Room type configuration for properties."""

    __tablename__ = "room_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    property_id: Mapped[int] = mapped_column(Integer, ForeignKey("properties.id"), nullable=False)
    room_type: Mapped[str] = mapped_column(SQLEnum(RoomType), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    max_guests: Mapped[int] = mapped_column(Integer, default=2)
    total_rooms: Mapped[int] = mapped_column(Integer, default=1)
    base_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    amenities: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    property: Mapped["Property"] = relationship("Property", back_populates="room_types")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="room_type")
    inventory_ledgers: Mapped[list["InventoryLedger"]] = relationship("InventoryLedger", back_populates="room_type")
