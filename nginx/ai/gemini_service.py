import json
import google.generativeai as genai
from typing import Dict, Optional

from config.api_config import API_CONFIG
from utils.logger import setup_logger

logger = setup_logger("gemini_service")

class GeminiService:
    """Integration with Gemini AI API for information enhancement"""
    
    def __init__(self):
        self.api_key = API_CONFIG["gemini"]["api_key"]
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def analyze_event(self, title: str, description: str, current_info: Dict = None) -> Optional[Dict]:
        """
        Analyze event information using Gemini API
        
        Args:
            title: Event title
            description: Event description text
            current_info: Currently extracted information (optional)
            
        Returns:
            Dictionary with enhanced information or None if analysis fails
        """
        try:
            # Create prompt for Gemini
            prompt = self._create_prompt(title, description, current_info)
            
            # Call Gemini API
            response = self.model.generate_content(prompt)
            
            # Parse response
            result = self._parse_json_response(response.text)
            if result:
                logger.info(f"Successfully analyzed event with Gemini: {title}")
                return result
            
            logger.warning(f"Failed to parse Gemini response for event: {title}")
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing event with Gemini: {e}")
            return None
    
    def _create_prompt(self, title: str, description: str, current_info: Dict = None) -> str:
        """Create prompt for Gemini API"""
        current_info_str = json.dumps(current_info, ensure_ascii=False, indent=2) if current_info else "{}"
        
        prompt = f"""
        다음 팝업스토어 정보를 분석하고 필요한 정보를 추출해주세요:

        제목: {title}

        설명: {description}

        현재 추출된 정보: {current_info_str}

        제목, 브랜드명, 시작일/종료일, 위치, 신뢰도를 다음과 같은 형식의 JSON으로 응답해주세요:

        ```json
        {{
            "title": "정확한 행사명",
            "brand": "브랜드명",
            "start_date": "YYYY-MM-DD",
            "end_date": "YYYY-MM-DD",
            "location": {{
                "place": "장소명 (예: 성수동 위즈엘)",
                "address": "정확한 주소"
            }},
            "confidence": 0.8,
            "reasoning": "판단 근거"
        }}
        ```
        날짜 정보가 명확하지 않으면 최대한 텍스트 내용을 기반으로 추정해주세요.
        위치 정보가 명확하지 않으면 '미정'으로 표시하고 confidence를 낮게 설정해주세요.
        confidence는 0.0부터 1.0 사이의 값으로, 정보의 확실성을 나타냅니다.
        """
        return prompt

    def _parse_json_response(self, text: str) -> Optional[Dict]:
        """Extract and parse JSON from Gemini response"""
        try:
            # Find JSON block in response
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = text[json_start:json_end]
                result = json.loads(json_str)
                
                # Validate required fields
                required_fields = ["title", "start_date", "location"]
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    logger.warning(f"Missing required fields in Gemini response: {missing_fields}")
                    return None
                
                # Ensure confidence is a float
                if "confidence" in result:
                    try:
                        result["confidence"] = float(result["confidence"])
                    except (ValueError, TypeError):
                        result["confidence"] = 0.5
                        
                return result
            
            return None
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing Gemini response: {e}")
            return None
