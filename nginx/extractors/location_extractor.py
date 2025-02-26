# extractors/location_extractor.py
import re
from typing import Dict, List, Optional

from utils.logger import setup_logger

logger = setup_logger("location_extractor")

class LocationExtractor:
    """Extracts location information from text"""
    
    def __init__(self):
        # Common venues and landmarks in Seongsu-dong
        self.venues = {
            "buildings": [
                "언더스탠드에비뉴", "대림창고", "에스팩토리", "성수연방", "성수동 아틀리에"
                "성수역", "서울숲역", "뚝섬역", "건대입구역",
                "아크앤북", "성수연방"
            ],
            "streets": [
                "연무장길", "성수이로", "성수일로", "서울숲2길", "서울숲4길"
            ],
            "areas": [
                "성수동", "서울숲", "성수", "뚝섬", "성동구"
            ]
        }
        
        # Brand stores in Seongsu-dong
        self.brand_stores = {
            "무신사": ["무신사 테라스", "무신사 스튜디오", "무신사 스토어"],
            "나이키": ["나이키 성수", "나이키 서울"],
            "아디다스": ["아디다스 성수"],
            "언더아머": ["언더아머 성수"],
            "아크네": ["아크네 스튜디오 성수"]
        }
        
        # Compile address patterns
        self.address_patterns = [
            r'서울\s*성동구\s*성수동\d가\s*\d+[가-힣\d\-]+',
            r'성수동\d가\s*\d+[가-힣\d\-]+',
            r'성동구\s*성수동\s*\d+[가-힣\d\-]+',
            r'서울\s*성동구\s*[\w\d]+로\s*\d+',
            r'서울시\s*성동구\s*[\w\d]+로\s*\d+'
        ]
    
    def extract_location(self, text: str) -> Optional[Dict]:
        """
        Extract location information from text
        
        Returns:
            Dictionary with place, address, and confidence level
            Or None if no location found
        """
        result = {
            "place": "미정",
            "address": "미정",
            "coordinates": {"lat": 0, "lng": 0},
            "transit": "",
            "confidence": 0.0
        }
        
        # Check for venue names
        venue_found = False
        for venue_type, venues in self.venues.items():
            for venue in venues:
                if venue in text:
                    result["place"] = venue
                    venue_found = True
                    result["confidence"] = 0.7
                    break
            if venue_found:
                break
        
        # Check for brand stores
        brand_found = False
        for brand, stores in self.brand_stores.items():
            if brand in text:
                for store in stores:
                    if store in text:
                        result["place"] = store
                        brand_found = True
                        result["confidence"] = 0.8
                        break
                
                if not brand_found:
                    # Brand name found but not specific store
                    result["place"] = f"{brand} 성수"
                    brand_found = True
                    result["confidence"] = 0.6
                break
        
        # Check for address patterns
        for pattern in self.address_patterns:
            matches = re.search(pattern, text)
            if matches:
                result["address"] = matches.group(0)
                result["confidence"] = max(result["confidence"], 0.9)
                break
        
        # Extract transit information
        transit_patterns = [
            r'성수역\s*\d+번\s*출구',
            r'서울숲역\s*\d+번\s*출구',
            r'뚝섬역\s*\d+번\s*출구'
        ]
        
        for pattern in transit_patterns:
            matches = re.search(pattern, text)
            if matches:
                result["transit"] = matches.group(0)
                break
        
        # Return None if confidence is too low and no specific location found
        if result["confidence"] < 0.1 and result["place"] == "미정" and result["address"] == "미정":
            return None
            
        return result
