import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # API
    API_VERSION = "1.0.0"
    
    # Data paths
    DATA_UPLOAD_DIR = os.getenv("DATA_UPLOAD_DIR", "./data/uploads")
    DATA_SAMPLE_DIR = os.getenv("DATA_SAMPLE_DIR", "./data/sample")
    
    # LLM
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    
    # Feature flags
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
