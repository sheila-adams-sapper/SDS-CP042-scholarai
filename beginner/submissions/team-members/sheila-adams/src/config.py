"""
Configuration management for ScholarAI.

This module loads environment variables and provides centralized access
to API keys and configuration settings throughout the application.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Centralized configuration class.
    
    This class loads all configuration from environment variables and provides
    validation to ensure required keys are present. It follows the singleton
    pattern to ensure consistent configuration across the application.
    """
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    #OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

    # Model configuration
    RESEARCH_MODEL: str = os.getenv("RESEARCH_MODEL", "gpt-4o-mini")  # Cheaper for tool calling
    SYNTHESIS_MODEL: str = os.getenv("SYNTHESIS_MODEL", "gpt-4o")     # Better quality for synthesis

    
    # Search API Configuration
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    SERPAPI_API_KEY: str = os.getenv("SERPAPI_API_KEY", "")
    
    # Application Settings
    DEFAULT_SEARCH_RESULTS: int = 10
    MAX_SEARCH_RESULTS: int = 20
    
    # Output Configuration
    OUTPUT_DIR: Path = Path("outputs")
    
    @classmethod
    def validate(cls) -> None:
        """
        Validate that required configuration is present.
        
        Raises:
            ValueError: If required API keys are missing.
        """
        if not cls.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is required. Please set it in your .env file."
            )
        
        if not cls.TAVILY_API_KEY and not cls.SERPAPI_API_KEY:
            raise ValueError(
                "At least one search API key (TAVILY_API_KEY or SERPAPI_API_KEY) "
                "is required. Please set it in your .env file."
            )
    
    @classmethod
    def get_search_provider(cls) -> str:
        """
        Determine which search provider to use based on available keys.
        
        Returns:
            str: Either 'tavily' or 'serpapi'
        """
        if cls.TAVILY_API_KEY:
            return "tavily"
        elif cls.SERPAPI_API_KEY:
            return "serpapi"
        else:
            raise ValueError("No search API key configured")
    
    @classmethod
    def ensure_output_dir(cls) -> None:
        """Create output directory if it doesn't exist."""
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# Validate configuration on import
try:
    Config.validate()
    Config.ensure_output_dir()
    print(f"✓ Configuration loaded. Using search provider: {Config.get_search_provider()}")
except ValueError as e:
    print(f"⚠️  Configuration warning: {e}")
