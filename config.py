"""
Configuration settings for the Report to Reveal backend
"""
from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    app_name: str = "Report to Reveal Analysis System"
    app_version: str = "1.0.0"
    api_prefix: str = "/api/v1"
    
    # OpenAI Configuration
    openai_api_key: str = ""  # Set via OPENAI_API_KEY environment variable or .env file
    openai_model: str = "gpt-4o"  # Must use gpt-4o or gpt-4o-mini for Structured Outputs
    skip_ai_analysis: bool = False  # Set to True to skip AI analysis for faster testing
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./report_to_reveal.db"
    
    # File Upload Configuration
    max_upload_size: int = 52428800  # 50MB
    allowed_extensions: List[str] = [".pdf", ".docx"]
    upload_dir: Path = Path("./uploads")
    results_dir: Path = Path("./results")
    temp_dir: Path = Path("./temp")
    
    # CORS Configuration - Allow specific origins + wildcards for development
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://document-parsing-frontend-git-main-content-generation.vercel.app",
        "https://*.vercel.app",  # All Vercel preview deployments
    ]
    
    # Email Configuration
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    from_email: str = ""
    admin_email: str = ""
    send_reports_automatically: bool = False  # If True, sends reports immediately; if False, admin reviews first
    
    # Security
    secret_key: str = "change-this-in-production"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.upload_dir.mkdir(exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)

# Create settings instance
settings = Settings()

# Load compliance rules
import json
COMPLIANCE_RULES_PATH = Path(__file__).parent.parent / "compliance_rules.json"
if COMPLIANCE_RULES_PATH.exists():
    with open(COMPLIANCE_RULES_PATH, "r") as f:
        COMPLIANCE_RULES = json.load(f)
else:
    # Default rules if file not found
    COMPLIANCE_RULES = {
        "parameters": {
            "critical_must_have": {},
            "problematic_avoid": {}
        },
        "critical_calculations": {},
        "scoring_weights": {
            "critical_parameter_present": 10,
            "critical_parameter_missing": -10,
            "critical_calculation_present": 15,
            "critical_calculation_missing": -15,
            "problematic_parameter_present": -5
        }
    }
