from pathlib import Path
import os
from dotenv import load_dotenv

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
if _ENV_FILE.is_file():
    load_dotenv(_ENV_FILE)
else:
    load_dotenv()

class Config:
    """Application configuration"""
    
    # API
    API_VERSION = "1.0.0"
    
    # Data paths
    DATA_UPLOAD_DIR = os.getenv("DATA_UPLOAD_DIR", "./data/uploads")
    DATA_SAMPLE_DIR = os.getenv("DATA_SAMPLE_DIR", "./data/sample")
    
    # LLM (Google Gemini)
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite-preview")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    
    # Feature flags
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
