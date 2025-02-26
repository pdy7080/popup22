# collectors/naver_collector.py
import requests
import json
import time
from typing import Dict, List, Optional
from urllib.parse import quote

from config.api_config import API_CONFIG
from utils.logger import setup_logger

logger = setup_logger("naver_collector")

class NaverCollector:
    """Collects information from Naver search API"""
    
    def __init__(self):
        self.api_url = API_CONFIG["naver_search"]["api_url"]
        self.client_id = API_CONFIG["naver_search"]["client_id"]
        self.client_secret = API_CONFIG["naver_search"]["client_secret"]
        
    def search(self, keyword: str, max_results: int = 20, sort: str = "date") -> List[Dict]:
        """
        Search for blog posts using the Naver API
        
        Args:
            keyword: Search keyword
            max_results: Maximum number of results to return
            sort: Sort order (date, sim)
            
        Returns:
            List of dictionaries with search results
        """
        try:
            encoded_keyword = quote(keyword)
            headers = {
                "X-Naver-Client-Id": self.client_id,
                "X-Naver-Client-Secret": self.client_secret
            }
            
            display = min(max_results, 100)  # Naver API allows max 100 results per request
            page_count = (max_results + display - 1) // display
            
            all_items = []
            
            for page in range(1, page_count + 1):
                url = f"{self.api_url}?query={encoded_keyword}&display={display}&start={1 + (page-1)*display}&sort={sort}"
                
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                items = data.get("items", [])
                
                # Process each item to standardize and clean data
                processed_items = [self.extract_info(item) for item in items]
                all_items.extend(processed_items)
                
                # Be nice to the API - add a short delay between requests
                if page < page_count:
                    time.sleep(0.5)
                    
            logger.info(f"Successfully collected {len(all_items)} items for keyword: {keyword}")
            return all_items
            
        except requests.RequestException as e:
            logger.error(f"Request error during Naver search: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error during Naver search: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during Naver search: {e}")
            return []
    
    def extract_info(self, item: Dict) -> Dict:
        """Extract and clean information from a search result item"""
        try:
            # Remove HTML tags from title and description
            import re
            
            title = re.sub(r'<[^>]+>', '', item.get('title', ''))
            description = re.sub(r'<[^>]+>', '', item.get('description', ''))
            
            # Standardize date format
            publish_date = item.get('postdate', '')
            
            # Create a standardized event dictionary
            event = {
                "title": title,
                "description": description,
                "link": item.get('link', ''),
                "source": "naver_blog",
                "published_at": publish_date,
                "blogger_name": item.get('bloggername', '')
            }
            
            logger.info(f"Successfully extracted event: {title}")
            return event
            
        except Exception as e:
            logger.error(f"Error extracting info from item: {e}")
            return item  # Return original item if extraction fails
