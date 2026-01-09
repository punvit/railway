"""Inventory model for stock tracking."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, DateTime, ForeignKey, Numeric, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.property import RoomType


class InventoryStatus(str, Enum):
    """Inventory status enum."""
    AVAILABLE = "available"
    RESERVED = "reserved"
    BLOCKED = "blocked"


class InventoryLedger(Base):
    """Inventory ledger model for tracking stock levels."""

    __tablename__ = "inventory_ledger"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("room_types.id"), nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    available_count: Mapped[int] = mapped_column(Integer, default=0)
    reserved_count: Mapped[int] = mapped_column(Integer, default=0)
    blocked_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(SQLEnum(InventoryStatus), default=InventoryStatus.AVAILABLE.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    room_type: Mapped["RoomType"] = relationship("RoomType", back_populates="inventory_ledgers")
