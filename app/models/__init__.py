"""Models package initialization."""
# Import all models here to ensure they are registered with Base.metadata
from app.models.booking import Booking
from app.models.channel import ChannelMapping
from app.models.inventory import InventoryLedger
from app.models.property import Property, RoomType
