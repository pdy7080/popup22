# processors/data_integrator.py
import re
from typing import Dict, List, Set, Tuple
from difflib import SequenceMatcher

from models.event import Event
from utils.logger import setup_logger

logger = setup_logger("data_integrator")

class DataIntegrator:
    """Integrates event data from multiple sources, removing duplicates"""
    
    def __init__(self):
        self.similarity_threshold = 0.7  # Title similarity threshold for duplicate detection
    
    def integrate_events(self, events: List[Event]) -> List[Event]:
        """
        Integrate events from multiple sources, removing duplicates
        
        Args:
            events: List of Event objects
            
        Returns:
            List of unique Event objects with merged information
        """
        if not events:
            return []
            
        try:
            # Group similar events
            event_groups = self._group_similar_events(events)
            
            # Merge events in each group
            merged_events = [self._merge_event_group(group) for group in event_groups]
            
            # Filter out None results (failed merges)
            unique_events = [event for event in merged_events if event]
            
            logger.info(f"Integrated {len(events)} events into {len(unique_events)} unique events")
            return unique_events
            
        except Exception as e:
            logger.error(f"Error integrating events: {e}")
            return events  # Return original events in case of error
    
    def _group_similar_events(self, events: List[Event]) -> List[List[Event]]:
        """Group similar events based on title and period similarity"""
        groups = []
        ungrouped = list(events)
        
        while ungrouped:
            # Take the first event as the reference
            reference = ungrouped.pop(0)
            group = [reference]
            
            # Find similar events
            i = 0
            while i < len(ungrouped):
                candidate = ungrouped[i]
                
                # Check if candidate is similar to reference
                if self._are_events_similar(reference, candidate):
                    group.append(ungrouped.pop(i))
                else:
                    i += 1
            
            groups.append(group)
        
        return groups
    
    def _are_events_similar(self, event1: Event, event2: Event) -> bool:
        """Check if two events are similar based on title and period"""
        # Check title similarity
        title_similarity = self._calculate_similarity(event1.title, event2.title)
        
        # If titles are very similar, consider them the same event
        if title_similarity > self.similarity_threshold:
            return True
            
        # If titles are somewhat similar, check period overlap
        if title_similarity > 0.5:
            # Check if periods overlap
            if event1.period.start_date and event2.period.start_date:
                # If dates match exactly, consider them the same event
                if (event1.period.start_date == event2.period.start_date and 
                    event1.period.end_date == event2.period.end_date):
                    return True
                    
                # Check for period overlap
                if self._periods_overlap(event1.period, event2.period):
                    # If periods overlap and location is similar, consider them the same
                    location_similarity = self._calculate_similarity(
                        event1.location.place, event2.location.place
                    )
                    if location_similarity > 0.7:
                        return True
        
        # Check if they have the same brand and similar period
        if event1.brand and event2.brand and event1.brand == event2.brand:
            if event1.period.start_date and event2.period.start_date:
                # If start dates are close (within 3 days)
                date_diff = abs((event1.period.start_date - event2.period.start_date).days)
                if date_diff <= 3:
                    return True
        
        return False
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity using SequenceMatcher"""
        if not str1 or not str2:
            return 0.0
            
        # Remove common punctuation and whitespace
        str1 = re.sub(r'[\s\-_,\.;:\'"!?]+', '', str1.lower())
        str2 = re.sub(r'[\s\-_,\.;:\'"!?]+', '', str2.lower())
        
        # Use SequenceMatcher for string similarity
        return SequenceMatcher(None, str1, str2).ratio()
    
    def _periods_overlap(self, period1, period2) -> bool:
        """Check if two periods overlap"""
        # If either period is missing start/end date, assume no overlap
        if not period1.start_date or not period2.start_date:
            return False
            
        # Define end dates, using start date if end date is missing
        end1 = period1.end_date or period1.start_date
        end2 = period2.end_date or period2.start_date
        
        # Check for overlap
        return (period1.start_date <= end2) and (period2.start_date <= end1)
    
    def _merge_event_group(self, group: List[Event]) -> Event:
        """Merge information from a group of similar events"""
        if not group:
            return None
            
        if len(group) == 1:
            return group[0]
            
        try:
            # Select the event with the highest confidence as the base
            base_event = max(group, key=lambda e: e.confidence)
            
            # Collect all source URLs
            source_urls = set()
            for event in group:
                source_urls.update(event.source_urls)
            
            # Find the most complete description
            longest_desc = ""
            for event in group:
                if event.details.introduction:
                    desc = " ".join(event.details.introduction)
                    if len(desc) > len(longest_desc):
                        longest_desc = desc
            
            # Create merged details
            merged_details = base_event.details
            if longest_desc and not merged_details.introduction:
                merged_details.introduction = [longest_desc]
            
            # Select the most specific location
            best_location = base_event.location
            for event in group:
                # Prefer locations with specific addresses
                if event.location.address != "미정" and best_location.address == "미정":
                    best_location = event.location
            
            # Create merged event
            merged_event = Event(
                title=base_event.title,
                brand=base_event.brand,
                period=base_event.period,
                location=best_location,
                operating_hours=base_event.operating_hours,
                details=merged_details,
                source_urls=list(source_urls),
                confidence=max(e.confidence for e in group),
                collected_at=base_event.collected_at
            )
            
            logger.info(f"Merged {len(group)} events into: {merged_event.title}")
            return merged_event
            
        except Exception as e:
            logger.error(f"Error merging event group: {e}")
            # Return the first event in case of error
            return group[0] if group else None
