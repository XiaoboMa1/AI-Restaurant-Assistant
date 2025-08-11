"""
Configuration Management Module - Unified management of all configuration items
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class Config:
    """Application configuration class"""
    
    # LLM Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip('"')
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo").strip('"')
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "").strip('"')
    
    # Restaurant API Configuration
    RESTAURANT_API_BASE_URL: str = os.getenv("RESTAURANT_API_BASE_URL", "http://localhost:8547")
    RESTAURANT_API_TOKEN: str = os.getenv("RESTAURANT_API_TOKEN", "")
    RESTAURANT_NAME: str = os.getenv("RESTAURANT_NAME", "TheHungryUnicorn")
    
    # Agent Behavior Configuration
    MAX_AVAILABILITY_SEARCH_DAYS: int = int(os.getenv("MAX_AVAILABILITY_SEARCH_DAYS", "20"))
    AGENT_MAX_ITERATIONS: int = int(os.getenv("AGENT_MAX_ITERATIONS", "15"))
    
    # Data storage configuration
    DATA_PATH: str = os.getenv("DATA_PATH", "data")
    
    @classmethod
    def validate(cls) -> None:
        """Validate that required configuration exists"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")
        if not cls.RESTAURANT_API_TOKEN:
            raise ValueError("RESTAURANT_API_TOKEN is required")
        if cls.MAX_AVAILABILITY_SEARCH_DAYS <= 0 or cls.MAX_AVAILABILITY_SEARCH_DAYS > 365:
            raise ValueError("MAX_AVAILABILITY_SEARCH_DAYS must be between 1 and 365")

# Global configuration instance
config = Config() 