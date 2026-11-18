"""
Configuration settings for Automated Multi-Platform Posting System using Pydantic BaseSettings.
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration and third-party platform credentials."""

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 4000
    ENVIRONMENT: str = "development"
    REQUEST_TIMEOUT: float = 15.0

    # Simulation Fallback (Allows testing without requiring paid/live API keys for all 5 platforms)
    ENABLE_SIMULATION_FALLBACK: bool = True

    # 1. Telegram Bot API
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None

    # 2. Discord Webhook API
    DISCORD_WEBHOOK_URL: Optional[str] = None

    # 3. Slack Incoming Webhook API
    SLACK_WEBHOOK_URL: Optional[str] = None

    # 4. Mastodon REST API
    MASTODON_ACCESS_TOKEN: Optional[str] = None
    MASTODON_INSTANCE_URL: str = "https://mastodon.social"

    # 5. Reddit OAuth2 API
    REDDIT_CLIENT_ID: Optional[str] = None
    REDDIT_CLIENT_SECRET: Optional[str] = None
    REDDIT_USERNAME: Optional[str] = None
    REDDIT_PASSWORD: Optional[str] = None
    REDDIT_SUBREDDIT: str = "test"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
