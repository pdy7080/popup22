# wordpress/wp_publisher.py
import requests
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from models.event import Event
from config.api_config import API_CONFIG
from utils.logger import setup_logger

logger = setup_logger("wp_publisher")

class WordPressPublisher:
    """Publishes event information to WordPress"""
    
    def __init__(self):
        self.wp_url = API_CONFIG["wordpress"]["url"]
        self.wp_username = API_CONFIG["wordpress"]["username"]
        self.wp_password = API_CONFIG["wordpress"]["password"]
        self.api_base = f"{self.wp_url}/wp-json/wp/v2"
    
    def publish_events(self, events: List[Event]) -> Dict:
        """
        Publish multiple events to WordPress
        
        Args:
            events: List of Event objects to publish
            
        Returns:
            Dictionary with success count and error count
        """
        results = {
            "success": 0,
            "error": 0,
            "skipped": 0
        }
        
        for event in events:
            try:
                # Check if event already exists
                if self._event_exists(event):
                    logger.info(f"Event already exists, skipping: {event.title}")
                    results["skipped"] += 1
                    continue
                
                # Publish event
                post_id = self._create_post(event)
                
                if post_id:
                    logger.info(f"Successfully published event: {event.title} (ID: {post_id})")
                    results["success"] += 1
                else:
                    logger.warning(f"Failed to publish event: {event.title}")
                    results["error"] += 1
                    
            except Exception as e:
                logger.error(f"Error publishing event {event.title}: {e}")
                results["error"] += 1
        
        return results
    
    def _event_exists(self, event: Event) -> bool:
        """Check if event already exists in WordPress"""
        try:
            # Check by title and date
            title_search = event.title.replace('"', '')
            
            # Format date for query
            start_date = event.period.start_date.strftime("%Y-%m-%d") if event.period.start_date else None
            
            # If no start date, can't check properly
            if not start_date:
                return False
            
            # Query WordPress API for existing posts with the same title
            url = f"{self.api_base}/posts?search={title_search}"
            response = requests.get(url)
            
            if response.status_code != 200:
                logger.error(f"Error checking if event exists: {response.text}")
                return False
                
            posts = response.json()
            
            for post in posts:
                # Check if post title matches
                if post['title']['rendered'] == event.title:
                    # Check if the post has the same event date
                    if 'meta' in post and 'event_date' in post['meta']:
                        if post['meta']['event_date'] == start_date:
                            return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking if event exists: {e}")
            return False
    
    def _create_post(self, event: Event) -> Optional[int]:
        """Create a WordPress post for an event"""
        try:
            # Create post content in HTML format
            post_content = self._format_post_content(event)
            
            # Format event period for title
            period_str = ""
            if event.period.start_date:
                period_str = f" ({event.period.start_date.strftime('%m/%d')}~"
                if event.period.end_date:
                    period_str += f"{event.period.end_date.strftime('%m/%d')}"
                period_str += ")"
            
            # Post data
            post_data = {
                "title": event.title + period_str,
                "content": post_content,
                "status": "publish",
                "categories": [8],  # Popup store category ID
                "meta": {
                    "event_start_date": event.period.start_date.strftime("%Y-%m-%d") if event.period.start_date else "",
                    "event_end_date": event.period.end_date.strftime("%Y-%m-%d") if event.period.end_date else "",
                    "event_location": event.location.place,
                    "event_address": event.location.address
                }
            }
            
            # Post request headers
            headers = {
                "Content-Type": "application/json"
            }
            
            # Post to WordPress
            url = f"{self.api_base}/posts"
            response = requests.post(
                url,
                headers=headers,
                json=post_data,
                auth=(self.wp_username, self.wp_password)
            )
            
            if response.status_code in (200, 201):
                post_id = response.json().get("id")
                return post_id
            else:
                logger.error(f"Error creating post: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating post: {e}")
            return None
    
    def _format_post_content(self, event: Event) -> str:
        """Format event information as HTML content"""
        # Start with period info
        period_info = "행사 기간: "
        if event.period.start_date:
            period_info += event.period.start_date.strftime("%Y년 %m월 %d일")
            if event.period.end_date:
                period_info += f" ~ {event.period.end_date.strftime('%Y년 %m월 %d일')}"
        else:
            period_info += "미정"
            
        # Location info
        location_info = f"장소: {event.location.place}"
        if event.location.address and event.location.address != "미정":
            location_info += f" ({event.location.address})"
            
        # Operating hours
        hours_info = ""
        if event.operating_hours.start and event.operating_hours.end:
            hours_info = f"운영 시간: {event.operating_hours.start} ~ {event.operating_hours.end}"
            
        # Introduction
        introduction = ""
        if event.details.introduction:
            introduction = "<h3>행사 소개</h3>"
            introduction += "<ul>"
            for intro in event.details.introduction:
                if intro:
                    introduction += f"<li>{intro}</li>"
            introduction += "</ul>"
            
        # Contents
        contents = ""
        if event.details.contents:
            contents = "<h3>주요 콘텐츠</h3>"
            contents += "<ul>"
            for content in event.details.contents:
                if content:
                    contents += f"<li>{content}</li>"
            contents += "</ul>"
            
        # Visitor info
        visitor_info = ""
        if event.details.visitor_info:
            visitor_info = "<h3>방문 정보</h3>"
            visitor_info += "<ul>"
            for info in event.details.visitor_info:
                if info:
                    visitor_info += f"<li>{info}</li>"
            visitor_info += "</ul>"
            
        # Transit info
        transit = ""
        if event.location.transit:
            transit = f"<p>교통 정보: {event.location.transit}</p>"
            
        # Source URLs
        sources = ""
        if event.source_urls:
            sources = "<h3>참고 링크</h3>"
            sources += "<ul>"
            for url in event.source_urls:
                if url:
                    sources += f'<li><a href="{url}" target="_blank">더 자세한 정보 보기</a></li>'
            sources += "</ul>"
            
        # Map iframe
        map_embed = ""
        if event.location.address and event.location.address != "미정":
            map_embed = f"""
            <h3>위치 지도</h3>
            <div class="map-container">
                <iframe 
                    width="100%" 
                    height="450" 
                    frameborder="0" 
                    style="border:0" 
                    src="https://www.google.com/maps/embed/v1/place?key=AIzaSyDfYlXeJ7A0T_fBH_iBjpJo9RFRt1wrHuE&q={event.location.address}" 
                    allowfullscreen>
                </iframe>
            </div>
            """
        
        # Combine all sections
        html_content = f"""
        <div class="event-info">
            <div class="event-meta">
                <p><strong>{period_info}</strong></p>
                <p><strong>{location_info}</strong></p>
                {f'<p><strong>{hours_info}</strong></p>' if hours_info else ''}
            </div>
            
            {introduction}
            {contents}
            {visitor_info}
            {transit}
            {sources}
            {map_embed}
            
            <p class="event-footer">
                <small>마지막 업데이트: {event.collected_at.strftime('%Y년 %m월 %d일')}</small>
            </p>
        </div>
        """
        
        return html_content