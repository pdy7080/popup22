
# extractors/date_extractor.py
import re
from datetime import datetime, timedelta
from typing import Dict, Optional

from utils.logger import setup_logger

logger = setup_logger("date_extractor")

class DateExtractor:
    """Extracts date information from text"""
    
    def __init__(self):
        self.year = datetime.now().year
        
    def extract_dates(self, text: str) -> Optional[Dict]:
        """
        Extract date information from text
        
        Supported formats:
        - YYYY-MM-DD
        - MM월 DD일
        - MM/DD or MM.DD
        - MM월 DD일부터 MM월 DD일까지
        - MM/DD~MM/DD
        
        Returns:
            Dictionary with start_date, end_date, and confidence level
            Or None if no dates found
        """
        # Priority order of patterns (explicit range first, then single dates)
        patterns = [
            # Explicit date ranges
            (r'(\d{1,2})월\s*(\d{1,2})일부터\s*(\d{1,2})월\s*(\d{1,2})일까지', 'explicit'),
            (r'(\d{1,2})[./](\d{1,2})\s*[\~\-]\s*(\d{1,2})[./](\d{1,2})', 'explicit'),
            
            # Month ranges
            (r'(\d{1,2})월\s*한달간', 'month'),
            (r'\~\s*(\d{1,2})[/월]\s*(\d{1,2})[일]*', 'month'),
            
            # Single dates (with year)
            (r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', 'single_with_year'),
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', 'single_with_year'),
            
            # Single dates (without year)
            (r'(\d{1,2})월\s*(\d{1,2})일', 'single'),
            (r'(\d{1,2})[./](\d{1,2})', 'single')
        ]
        
        for pattern, date_type in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                try:
                    if date_type == 'explicit':
                        # Handle explicit date range
                        m1, d1, m2, d2 = map(int, match.groups())
                        
                        start_date = datetime(self.year, m1, d1)
                        end_date = datetime(self.year, m2, d2)
                        
                        # Handle year boundary
                        if end_date < start_date:
                            if m1 > m2:  # Crosses year boundary
                                end_date = datetime(self.year + 1, m2, d2)
                        
                        return {
                            "start_date": start_date.strftime("%Y-%m-%d"),
                            "end_date": end_date.strftime("%Y-%m-%d"),
                            "type": "explicit",
                            "confidence": 0.9
                        }
                    
                    elif date_type == 'month':
                        # Handle month-based patterns
                        if 'month' in pattern:
                            # "N월 한달간" pattern
                            month = int(match.group(1))
                            start_date = datetime(self.year, month, 1)
                            last_day = 28
                            if month in [1, 3, 5, 7, 8, 10, 12]:
                                last_day = 31
                            elif month in [4, 6, 9, 11]:
                                last_day = 30
                            elif month == 2:
                                # Simplified leap year logic
                                last_day = 29 if self.year % 4 == 0 and (self.year % 100 != 0 or self.year % 400 == 0) else 28
                            
                            end_date = datetime(self.year, month, last_day)
                        else:
                            # "~MM/DD" pattern
                            month = int(match.group(1))
                            day = int(match.group(2))
                            end_date = datetime(self.year, month, day)
                            
                            # Assume current date as start date
                            start_date = datetime.now()
                            
                            # If end date is before today, it's likely for next year
                            if end_date < start_date:
                                end_date = datetime(self.year + 1, month, day)
                        
                        return {
                            "start_date": start_date.strftime("%Y-%m-%d"),
                            "end_date": end_date.strftime("%Y-%m-%d"),
                            "type": "month",
                            "confidence": 0.7
                        }
                    
                    elif date_type == 'single_with_year':
                        # Handle single date with year
                        if '-' in pattern:
                            year, month, day = map(int, match.groups())
                        else:
                            year, month, day = map(int, match.groups())
                            
                        start_date = datetime(year, month, day)
                        # For single dates, assume a 7-day event by default
                        end_date = start_date + timedelta(days=7)
                        
                        return {
                            "start_date": start_date.strftime("%Y-%m-%d"),
                            "end_date": end_date.strftime("%Y-%m-%d"),
                            "type": "single_with_year",
                            "confidence": 0.8
                        }
                    
                    elif date_type == 'single':
                        # Handle single date without year
                        month, day = map(int, match.groups())
                        start_date = datetime(self.year, month, day)
                        
                        # If date is in the past, it's likely for next year
                        if start_date < datetime.now() - timedelta(days=3):  # 3-day buffer
                            start_date = datetime(self.year + 1, month, day)
                            
                        # For single dates, assume a 7-day event by default
                        end_date = start_date + timedelta(days=7)
                        
                        return {
                            "start_date": start_date.strftime("%Y-%m-%d"),
                            "end_date": end_date.strftime("%Y-%m-%d"),
                            "type": "single",
                            "confidence": 0.6
                        }
                        
                except Exception as e:
                    logger.error(f"Error processing date match: {e}")
                    continue
        
        return None