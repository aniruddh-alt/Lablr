from pydantic_settings import BaseSettings
from typing import Optional
import os

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
    azure_cognitive_services_endpoint: Optional[str] = os.getenv("AZURE_COGNITIVE_SERVICES_ENDPOINT")
    azure_cognitive_services_key: Optional[str] = os.getenv("AZURE_COGNITIVE_SERVICES_KEY")
    azure_ml_workspace_name: Optional[str] = os.getenv("AZURE_ML_WORKSPACE_NAME")
    azure_ml_resource_group: Optional[str] = os.getenv("AZURE_ML_RESOURCE_GROUP")
    azure_ml_subscription_id: Optional[str] = os.getenv("AZURE_ML_SUBSCRIPTION_ID")
    
    # Service Bus
    service_bus_connection_string: Optional[str] = os.getenv("SERVICE_BUS_CONNECTION_STRING")
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    access_token_expire_minutes: int = 30
    
    # File Storage
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    upload_dir: str = "uploads"
    
    # Processing
    max_concurrent_jobs: int = 10
    job_timeout: int = 3600  # 1 hour
    
    class Config:
        env_file = ".env"
        case_sensitive = False

def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
