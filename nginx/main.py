# main.py
import json
import os
import argparse
from datetime import datetime
from typing import Dict, List

from collectors.naver_collector import NaverCollector
from processors.event_processor import EventProcessor
from processors.data_integrator import DataIntegrator
from wordpress.wp_publisher import WordPressPublisher
from config.api_config import SEARCH_CONFIG
from utils.logger import setup_logger

logger = setup_logger("main")

def collect_events() -> List[Dict]:
    """Collect event information from various sources"""
    logger.info("Starting event collection")
    
    # Initialize collector
    collector = NaverCollector()
    
    # Collect events from each keyword
    all_events = []
    
    for keyword in SEARCH_CONFIG["keywords"]:
        logger.info(f"Searching for keyword: {keyword}")
        events = collector.search(
            keyword=keyword,
            max_results=SEARCH_CONFIG["max_results_per_keyword"],
            sort=SEARCH_CONFIG["sort"]
        )
        all_events.extend(events)
        logger.info(f"Found {len(events)} events for keyword: {keyword}")
    
    logger.info(f"Total raw events collected: {len(all_events)}")
    return all_events

def process_events(raw_events: List[Dict]) -> List:
    """Process raw events into structured Event objects"""
    logger.info("Processing events")
    
    # Initialize processor
    processor = EventProcessor()
    
    # Process each event
    processed_events = []
    
    for raw_event in raw_events:
        event = processor.process_event(raw_event)
        if event:
            processed_events.append(event)
    
    logger.info(f"Successfully processed {len(processed_events)} events")
    return processed_events

def integrate_events(events) -> List:
    """Integrate events from multiple sources, removing duplicates"""
    logger.info("Integrating events")
    
    # Initialize integrator
    integrator = DataIntegrator()
    
    # Integrate events
    unique_events = integrator.integrate_events(events)
    
    logger.info(f"Integrated into {len(unique_events)} unique events")
    return unique_events

def save_events(events, publish=False):
    """Save events to JSON file and optionally publish to WordPress"""
    logger.info("Saving events")
    
    # Create output directory if it doesn't exist
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    year_month = datetime.now().strftime('%Y%m')
    output_dir = f"output/{year_month}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert events to dictionaries
    event_dicts = [event.to_dict() for event in events]
    
    # Save to JSON file
    output_file = f"{output_dir}/popup_events_{timestamp}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": timestamp,
            "total_events": len(events),
            "events": event_dicts
        }, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Events saved to {output_file}")
    
    # Publish to WordPress if requested
    if publish:
        logger.info("Publishing events to WordPress")
        publisher = WordPressPublisher()
        results = publisher.publish_events(events)
        logger.info(f"Publishing results: {results}")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Popup Store Event Collector')
    parser.add_argument('--publish', action='store_true', help='Publish events to WordPress')
    parser.add_argument('--file', type=str, help='Process events from a JSON file instead of collecting new ones')
    args = parser.parse_args()
    
    try:
        if args.file:
            # Load events from file
            logger.info(f"Loading events from file: {args.file}")
            with open(args.file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                raw_events = data.get("events", [])
            
            logger.info(f"Loaded {len(raw_events)} events from file")
        else:
            # Collect new events
            raw_events = collect_events()
        
        # Process events
        processed_events = process_events(raw_events)
        
        # Integrate events
        unique_events = integrate_events(processed_events)
        
        # Save and optionally publish events
        save_events(unique_events, publish=args.publish)
        
        logger.info("Event collection and processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}", exc_info=True)

if __name__ == "__main__":
    main()
