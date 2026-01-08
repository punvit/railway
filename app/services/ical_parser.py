"""iCal parser for Airbnb calendar synchronization."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class BlockedDateRange:
    """Represents a blocked date range from iCal."""
    start_date: date
    end_date: date
    summary: Optional[str] = None
    uid: Optional[str] = None


class ICalParser:
    """
    Parser for iCal (ICS) format calendars.
    
    Used primarily for Airbnb calendar synchronization where
    blocked dates are exposed via iCal feeds.
    """
    
    def parse_ical(self, ical_content: str) -> List[BlockedDateRange]:
        """
        Parse iCal content and extract blocked date ranges.
        
        Args:
            ical_content: Raw iCal file content
            
        Returns:
            List of BlockedDateRange objects
        """
        blocked_ranges = []
        
        try:
            # Simple parser - in production use icalendar library
            lines = ical_content.strip().split("\n")
            current_event = {}
            in_event = False
            
            for line in lines:
                line = line.strip()
                
                if line == "BEGIN:VEVENT":
                    in_event = True
                    current_event = {}
                elif line == "END:VEVENT":
                    in_event = False
                    if "DTSTART" in current_event and "DTEND" in current_event:
                        blocked_ranges.append(
                            BlockedDateRange(
                                start_date=current_event["DTSTART"],
                                end_date=current_event["DTEND"],
                                summary=current_event.get("SUMMARY"),
                                uid=current_event.get("UID"),
                            )
                        )
                elif in_event and ":" in line:
                    key, value = line.split(":", 1)
                    # Handle date format
                    if key in ("DTSTART", "DTEND") or key.startswith("DTSTART;") or key.startswith("DTEND;"):
                        base_key = "DTSTART" if "DTSTART" in key else "DTEND"
                        current_event[base_key] = self._parse_date(value)
                    elif key in ("SUMMARY", "UID"):
                        current_event[key] = value
            
        except Exception as e:
            logger.error(f"Error parsing iCal: {e}")
        
        return blocked_ranges
    
    def _parse_date(self, date_str: str) -> date:
        """Parse iCal date string to date object."""
        # Remove any value parameters
        date_str = date_str.strip()
        
        # Handle different date formats
        if "T" in date_str:
            # DateTime format: 20260115T120000
            dt = datetime.strptime(date_str[:8], "%Y%m%d")
        else:
            # Date only format: 20260115
            dt = datetime.strptime(date_str[:8], "%Y%m%d")
        
        return dt.date()
    
    def generate_sample_ical(
        self,
        blocked_ranges: List[BlockedDateRange],
    ) -> str:
        """
        Generate sample iCal content for testing.
        
        Args:
            blocked_ranges: List of date ranges to block
            
        Returns:
            iCal formatted string
        """
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Hotel Channel Manager//Test//EN",
        ]
        
        for i, block in enumerate(blocked_ranges):
            lines.extend([
                "BEGIN:VEVENT",
                f"UID:block-{i}@channelmanager.test",
                f"DTSTART;VALUE=DATE:{block.start_date.strftime('%Y%m%d')}",
                f"DTEND;VALUE=DATE:{block.end_date.strftime('%Y%m%d')}",
                f"SUMMARY:{block.summary or 'Blocked'}",
                "END:VEVENT",
            ])
        
        lines.append("END:VCALENDAR")
        return "\n".join(lines)


async def sync_airbnb_calendar(
    ical_url: str,
    room_type_id: int,
    db_session,
) -> dict:
    """
    Sync blocked dates from Airbnb iCal feed.
    
    Args:
        ical_url: URL to Airbnb iCal feed
        room_type_id: Local room type ID
        db_session: Database session
        
    Returns:
        Sync result with blocked date count
    """
    import httpx
    from sqlalchemy import select, and_
    from app.models.inventory import InventoryLedger
    
    try:
        # Fetch iCal content
        async with httpx.AsyncClient() as client:
            response = await client.get(ical_url, timeout=30)
            response.raise_for_status()
            ical_content = response.text
        
        # Parse blocked dates
        parser = ICalParser()
        blocked_ranges = parser.parse_ical(ical_content)
        
        # Update inventory to reflect blocked dates
        dates_blocked = 0
        for block in blocked_ranges:
            current = block.start_date
            while current < block.end_date:
                result = await db_session.execute(
                    select(InventoryLedger).where(
                        and_(
                            InventoryLedger.room_type_id == room_type_id,
                            InventoryLedger.date == current,
                        )
                    )
                )
                inventory = result.scalar_one_or_none()
                
                if inventory and inventory.available_rooms > 0:
                    inventory.available_rooms = 0  # Block the date
                    inventory.version += 1
                    dates_blocked += 1
                
                current = current + timedelta(days=1)
        
        await db_session.flush()
        
        return {
            "success": True,
            "blocked_ranges": len(blocked_ranges),
            "dates_blocked": dates_blocked,
        }
        
    except Exception as e:
        logger.error(f"Error syncing Airbnb calendar: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# Import needed for sync function
from datetime import timedelta
