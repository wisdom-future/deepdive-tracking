"""Application settings and configuration management."""

import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings

# Load secrets from GCP Secret Manager if available
try:
    from src.utils.gcp_secrets import load_gcp_secrets_to_env
    load_gcp_secrets_to_env()
except Exception as e:
    print(f"Warning: Could not load GCP secrets: {e}")


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "DeepDive Tracking"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # Server
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    api_version: str = "v1"

    # Database
    database_url: str = "sqlite:///./data/db/deepdive_tracking.db"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_timeout: int = 30

    # Redis Cache
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 3600

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # External APIs - OpenAI
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"
    openai_temperature: float = 0.3
    openai_max_tokens: int = 1000

    # External APIs - Grok (xAI)
    xai_api_key: Optional[str] = None
    xai_model: str = "grok-beta"
    xai_base_url: str = "https://api.x.ai/v1"

    # AI Provider Selection: "openai" or "grok"
    ai_provider: str = "grok"  # Default to Grok to avoid OpenAI bias

    # Web Crawling
    request_timeout: int = 30
    max_concurrent_requests: int = 10
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )

    # Content Processing
    min_content_length: int = 100
    max_content_length: int = 100000
    similarity_threshold: float = 0.8

    # Publishing Channels - WeChat
    wechat_api_url: Optional[str] = None
    wechat_app_id: Optional[str] = None
    wechat_app_secret: Optional[str] = None

    # Publishing Channels - GitHub
    github_token: Optional[str] = None
    github_repo: Optional[str] = None
    github_username: Optional[str] = None
    github_local_path: Optional[str] = None

    # Publishing Channels - Email
    smtp_host: Optional[str] = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: Optional[str] = os.getenv("SMTP_USER")
    smtp_password: Optional[str] = os.getenv("SMTP_PASSWORD")
    smtp_from_email: Optional[str] = os.getenv("SMTP_FROM_EMAIL") or os.getenv("SMTP_USER")
    smtp_from_name: str = os.getenv("SMTP_FROM_NAME", "DeepDive Tracking")
    email_list: Optional[list] = None

    xiaohongshu_api_url: Optional[str] = None
    xiaohongshu_token: Optional[str] = None

    # Admin User
    admin_username: str = "admin"
    admin_password: str = "admin_password"

    # Security
    secret_key: str = "your_secret_key_change_in_production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Feature Flags
    enable_ai_scoring: bool = True
    enable_duplicate_detection: bool = True
    enable_auto_publishing: bool = False
    enable_analytics: bool = True

    # Notifications
    notification_email: Optional[str] = None
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get application settings singleton.

    Returns:
        Settings: Application configuration instance.
    """
    return Settings()
