import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
    NVIDIA_BASE_URL: str = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    NVIDIA_MODEL_NAME: str = os.getenv("NVIDIA_MODEL_NAME", "meta/llama-3.3-70b-instruct")
    
    FASTAPI_HOST: str = os.getenv("FASTAPI_HOST", "0.0.0.0")
    FASTAPI_PORT: int = int(os.getenv("FASTAPI_PORT", "8000"))
    
    SELENIUM_HEADLESS: bool = os.getenv("SELENIUM_HEADLESS", "true").lower() == "true"
    MAX_SUBPAGES_PER_DOMAIN: int = int(os.getenv("MAX_SUBPAGES_PER_DOMAIN", "4"))
    PAGE_LOAD_TIMEOUT: int = int(os.getenv("PAGE_LOAD_TIMEOUT", "20"))
    
    # Cost estimation: NVIDIA NIM API rate / estimated standard model pricing per 1K tokens
    PROMPT_COST_PER_1K: float = 0.0007
    COMPLETION_COST_PER_1K: float = 0.0009

settings = Settings()
