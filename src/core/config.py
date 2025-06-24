from pydantic_settings import BaseSettings
from typing import Optional, List
import os
import json

class Settings(BaseSettings):
    """Application settings and configuration."""
    
    # Application
    app_name: str = "Lablr"
    debug: bool = False
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://lablr:lablr_dev_password@localhost/lablr")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Azure Services
    azure_storage_connection_string: Optional[str] = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    azure_form_recognizer_endpoint: Optional[str] = os.getenv("AZURE_FORM_RECOGNIZER_ENDPOINT")
    azure_form_recognizer_key: Optional[str] = os.getenv("AZURE_FORM_RECOGNIZER_KEY")
    
    # Azure OpenAI Services
    azure_openai_endpoint: Optional[str] = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_openai_key: Optional[str] = os.getenv("AZURE_OPENAI_KEY")
    azure_openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    azure_openai_deployment_name: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
    
    # Legacy naming for backward compatibility
    azure_cognitive_services_endpoint: Optional[str] = os.getenv("AZURE_COGNITIVE_SERVICES_ENDPOINT")
    azure_cognitive_services_key: Optional[str] = os.getenv("AZURE_COGNITIVE_SERVICES_KEY")
    
    # Azure ML
    azure_ml_workspace_name: Optional[str] = os.getenv("AZURE_ML_WORKSPACE_NAME")
    azure_ml_resource_group: Optional[str] = os.getenv("AZURE_ML_RESOURCE_GROUP")
    azure_ml_subscription_id: Optional[str] = os.getenv("AZURE_ML_SUBSCRIPTION_ID")
    
    # Service Bus
    service_bus_connection_string: Optional[str] = os.getenv("SERVICE_BUS_CONNECTION_STRING")
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    access_token_expire_minutes: int = 30
    
    # File Storage
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", 50 * 1024 * 1024))  # 50MB
    upload_dir: str = os.getenv("UPLOAD_DIR", "uploads")
    output_dir: str = os.getenv("OUTPUT_DIR", "outputs")
    
    # Processing
    max_concurrent_jobs: int = int(os.getenv("MAX_CONCURRENT_JOBS", 10))
    job_timeout: int = int(os.getenv("JOB_TIMEOUT", 3600))  # 1 hour
    batch_size: int = int(os.getenv("BATCH_SIZE", 5))
    
    # API Settings
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", 8000))
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS
    cors_origins: List[str] = []
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **data):
        super().__init__(**data)
        # Parse cors_origins from environment variable if it exists
        cors_env = os.getenv("CORS_ORIGINS")
        if cors_env:
            try:
                self.cors_origins = json.loads(cors_env)
            except:
                self.cors_origins = ["http://localhost:3000", "http://localhost:8080"]

def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
