"""
Configuration management for MoatTutor backend.

Uses Pydantic Settings to load and validate environment variables.
"""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings are loaded from .env file or environment variables.
    See env.example for available configuration options.
    """
    
    # LLM Provider Configuration
    llm_provider: str = Field(default="openai", description="LLM provider (openai or local)")
    llm_streaming: bool = Field(default=True, description="Enable streaming responses")
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., description="OpenAI API key (required)")
    openai_model: str = Field(default="gpt-5-nano", description="OpenAI model to use")
    
    # Local Model Configuration
    local_model_name: str = Field(default="llama3", description="Local model name for Ollama")
    local_model_base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL for local model API"
    )
    
    # Streaming Configuration
    stream_token_delay_ms: int = Field(
        default=0,
        description="Artificial delay between stream tokens (for testing)"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables
    )


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure settings are only loaded once.
    
    Returns:
        Cached Settings instance
    """
    return Settings()

