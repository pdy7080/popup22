# config/api_config.py
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_CONFIG = {
    "naver_search": {
        "client_id": os.getenv("NAVER_CLIENT_ID"),
        "client_secret": os.getenv("NAVER_CLIENT_SECRET"),
        "api_url": "https://openapi.naver.com/v1/search/blog.json"
    },
    "gemini": {
        "api_key": os.getenv("GEMINI_API_KEY")
    },
    "wordpress": {
        "url": os.getenv("WORDPRESS_URL"),
        "username": os.getenv("WORDPRESS_USERNAME"),
        "password": os.getenv("WORDPRESS_PASSWORD")
    }
}

SEARCH_CONFIG = {
    "keywords": [
        "성수동 팝업스토어",
        "성수 팝업",
        "서울숲 팝업스토어"
    ],
    "max_results_per_keyword": 20,
    "sort": "date"  # Sort by date (most recent first)
}
