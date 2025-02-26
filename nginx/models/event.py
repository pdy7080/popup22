# models/event.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

@dataclass
class EventLocation:
    """Location information for an event"""
    place: str = "미정"  # Default: Undetermined
    address: str = "미정"
    coordinates: Dict[str, float] = field(default_factory=lambda: {"lat": 0.0, "lng": 0.0})
    transit: str = ""  # Transportation information

@dataclass
class EventPeriod:
    """Time period for an event"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    def is_valid(self) -> bool:
        """Check if the period is valid"""
        return self.start_date is not None

    def is_active(self) -> bool:
        """Check if the event is currently active"""
        now = datetime.now()
        if not self.is_valid():
            return False
        if self.end_date:
            return self.start_date <= now <= self.end_date
        return self.start_date <= now

@dataclass
class EventDetails:
    """Additional details about an event"""
    introduction: List[str] = field(default_factory=list)
    contents: List[str] = field(default_factory=list)
    visitor_info: List[str] = field(default_factory=list)
    
@dataclass
class OperatingHours:
    """Operating hours for an event"""
    start: str = ""
    end: str = ""
    
@dataclass
class Event:
    """Popup store event information"""
    title: str
    brand: str = ""
    period: EventPeriod = field(default_factory=EventPeriod)
    location: EventLocation = field(default_factory=EventLocation)
    operating_hours: OperatingHours = field(default_factory=OperatingHours)
    details: EventDetails = field(default_factory=EventDetails)
    source_urls: List[str] = field(default_factory=list)
    confidence: float = 0.0
    collected_at: datetime = field(default_factory=datetime.now)
    
    def is_valid(self) -> bool:
        """Check if the event has essential information"""
        return (
            bool(self.title) and 
            self.period.is_valid() and 
            bool(self.location.place)
        )
    
    def to_dict(self) -> Dict:
        """Convert event to dictionary format"""
        return {
            "title": self.title,
            "brand": self.brand,
            "period": {
                "start_date": self.period.start_date.strftime("%Y-%m-%d") if self.period.start_date else None,
                "end_date": self.period.end_date.strftime("%Y-%m-%d") if self.period.end_date else None
            },
            "location": {
                "place": self.location.place,
                "address": self.location.address,
                "coordinates": self.location.coordinates,
                "transit": self.location.transit
            },
            "operating_hours": {
                "start": self.operating_hours.start,
                "end": self.operating_hours.end
            },
            "details": {
                "introduction": self.details.introduction,
                "contents": self.details.contents,
                "visitor_info": self.details.visitor_info
            },
            "source_urls": self.source_urls,
            "confidence": self.confidence,
            "collected_at": self.collected_at.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Event':
        """Create an Event from dictionary data"""
        event = cls(title=data.get("title", ""))
        
        # Handle period
        if "period" in data:
            start_str = data["period"].get("start_date")
            end_str = data["period"].get("end_date")
            
            event.period.start_date = datetime.strptime(start_str, "%Y-%m-%d") if start_str else None
            event.period.end_date = datetime.strptime(end_str, "%Y-%m-%d") if end_str else None
        
        # Handle location
        if "location" in data:
            event.location.place = data["location"].get("place", "미정")
            event.location.address = data["location"].get("address", "미정")
            event.location.coordinates = data["location"].get("coordinates", {"lat": 0.0, "lng": 0.0})
            event.location.transit = data["location"].get("transit", "")
        
        # Handle other fields
        event.brand = data.get("brand", "")
        
        if "operating_hours" in data:
            event.operating_hours.start = data["operating_hours"].get("start", "")
            event.operating_hours.end = data["operating_hours"].get("end", "")
            
        if "details" in data:
            event.details.introduction = data["details"].get("introduction", [])
            event.details.contents = data["details"].get("contents", [])
            event.details.visitor_info = data["details"].get("visitor_info", [])
        
        event.source_urls = data.get("source_urls", [])
        event.confidence = data.get("confidence", 0.0)
        
        collected_at = data.get("collected_at")
        if collected_at:
            try:
                event.collected_at = datetime.strptime(collected_at, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
        
        return event
