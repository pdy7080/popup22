from typing import Dict, List, Optional
from datetime import datetime

from models.event import Event, EventPeriod, EventLocation, OperatingHours, EventDetails
from extractors.date_extractor import DateExtractor
from extractors.location_extractor import LocationExtractor
from ai.gemini_service import GeminiService
from utils.logger import setup_logger

logger = setup_logger("event_processor")

class EventProcessor:
    """Processes and enriches event information"""
    
    def __init__(self):
        self.date_extractor = DateExtractor()
        self.location_extractor = LocationExtractor()
        self.gemini_service = GeminiService()
    
    def process_event(self, raw_event: Dict) -> Optional[Event]:
        """
        Process a raw event into a structured Event object
        
        Args:
            raw_event: Dictionary with raw event information
            
        Returns:
            Event object or None if processing fails
        """
        try:
            title = raw_event.get("title", "")
            description = raw_event.get("description", "")
            
            # Skip events that are clearly not popup stores
            if not self._is_likely_popup_store(title, description):
                logger.info(f"Skipping non-popup store event: {title}")
                return None
            
            # Try to extract core information using regular expressions first
            date_info = self.date_extractor.extract_dates(description) or self.date_extractor.extract_dates(title)
            location_info = self.location_extractor.extract_location(description) or self.location_extractor.extract_location(title)
            
            # Create preliminary event object
            event = self._create_preliminary_event(
                title=title, 
                description=description,
                date_info=date_info,
                location_info=location_info,
                source_url=raw_event.get("link", "")
            )
            
            # Try to enhance information using Gemini AI
            enhanced_event = self._enhance_with_ai(event, title, description)
            
            # Return the enhanced event or the original if enhancement failed
            result = enhanced_event if enhanced_event else event
            
            # Validate the event
            if self._is_valid_event(result):
                logger.info(f"Successfully processed event: {result.title}")
                return result
                
            logger.warning(f"Event validation failed: {result.title}")
            return None
            
        except Exception as e:
            logger.error(f"Error processing event: {e}")
            return None
    
    def _is_likely_popup_store(self, title: str, description: str) -> bool:
        """Check if the event is likely a popup store"""
        combined_text = (title + " " + description).lower()
        
        # Keywords that suggest popup stores
        popup_keywords = [
            "팝업", "팝업스토어", "pop-up", "popup", "pop up", 
            "프리오픈", "오픈", "open", "런칭", "시즌", "한정"
        ]
        
        return any(keyword in combined_text for keyword in popup_keywords)
    
    def _create_preliminary_event(self, title: str, description: str, date_info: Optional[Dict], location_info: Optional[Dict], source_url: str) -> Event:
        """Create preliminary Event object from extracted information"""
        period = EventPeriod(
            start_date=date_info.get("start_date"),
            end_date=date_info.get("end_date")
        ) if date_info else None
        
        location = EventLocation(
            place=location_info.get("place"),
            address=location_info.get("address")
        ) if location_info else None
        
        return Event(
            title=title,
            description=description,
            period=period,
            location=location,
            source_url=source_url
        )
    
    def _enhance_with_ai(self, event: Event, title: str, description: str) -> Optional[Event]:
        """Enhance event information using Gemini AI"""
        ai_info = self.gemini_service.analyze_event(title, description)
        
        if ai_info:
            # Update event with AI-enhanced information
            event.brand = ai_info.get("brand")
            event.period.start_date = ai_info.get("start_date") or event.period.start_date
            event.period.end_date = ai_info.get("end_date") or event.period.end_date
            event.location.place = ai_info.get("location", {}).get("place") or event.location.place
            event.location.address = ai_info.get("location", {}).get("address") or event.location.address
            event.confidence = ai_info.get("confidence", event.confidence)
            event.reasoning = ai_info.get("reasoning")
            
            return event
        
        return None
    
    def _is_valid_event(self, event: Event) -> bool:
        """Validate the event object"""
        required_fields = ["title", "period", "location"]
        
        for field in required_fields:
            if not getattr(event, field):
                logger.warning(f"Event is missing required field: {field}")
                return False
        
        return True

