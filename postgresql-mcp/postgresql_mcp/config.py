"""
Configuration management for PostgreSQL MCP Server.
Loads settings from environment variables with sensible defaults.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # PostgreSQL Configuration
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(..., alias="POSTGRES_DB")
    postgres_user: str = Field(..., alias="POSTGRES_USER")
    postgres_password: str = Field(..., alias="POSTGRES_PASSWORD")
    postgres_ssl_mode: str = Field(default="prefer", alias="POSTGRES_SSL_MODE")
    
    # Connection Pool Settings
    postgres_min_pool_size: int = Field(default=5, alias="POSTGRES_MIN_POOL_SIZE")
    postgres_max_pool_size: int = Field(default=20, alias="POSTGRES_MAX_POOL_SIZE")
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    
    # Server Configuration
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def postgres_dsn(self) -> str:
        """Construct PostgreSQL Data Source Name."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            f"?sslmode={self.postgres_ssl_mode}"
        )


# Global settings instance
settings = Settings()

