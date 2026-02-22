"""
Centralised configuration via pydantic-settings.
All secrets are loaded from .env — never hardcoded.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Telegram ─────────────────────────────────────
    bot_token: SecretStr = Field(..., description="Telegram Bot API token")
    admin_ids: List[int] = Field(default_factory=list, description="Comma-separated admin IDs")
    webhook_secret: SecretStr = Field(default=SecretStr(""), description="Webhook secret token")
    webhook_url: str = Field(default="", description="Public webhook URL (empty = polling)")

    # ── Database (PostgreSQL) ────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://vpnbot:secret@localhost:5432/vpnbot",
        description="Async SQLAlchemy DSN",
    )

    # ── Redis ────────────────────────────────────────
    redis_url: str = Field(default="redis://localhost:6379/0")

    # ── 3x-ui Panel ─────────────────────────────────
    xui_base_url: str = Field(default="", description="3x-ui panel URL")
    xui_username: str = Field(default="", description="3x-ui login")
    xui_password: SecretStr = Field(default=SecretStr(""), description="3x-ui password")
    xui_ssl_verify: bool = Field(default=True, description="Verify SSL for panel")
    xui_timeout: int = Field(default=15, description="HTTP timeout in seconds")
    xui_retry_attempts: int = Field(default=3, description="Retry count for API calls")
    xui_inbound_cache_ttl: int = Field(default=60, description="Inbound cache TTL in seconds")

    # ── Subscription ────────────────────────────────
    subscription_domain: str = Field(default="your.domain")

    # ── CryptoBot ───────────────────────────────────
    cryptobot_token: SecretStr = Field(default=SecretStr(""), description="CryptoBot API token")
    cryptobot_network: str = Field(default="mainnet", description="mainnet or testnet")

    # ── Pricing ─────────────────────────────────────
    stars_7_days: int = Field(default=10)
    stars_30_days: int = Field(default=11)
    crypto_7_days: float = Field(default=1.0)
    crypto_30_days: float = Field(default=3.0)

    # ── Rate Limiting ───────────────────────────────
    rate_limit_per_minute: int = Field(default=30)
    rate_limit_burst: int = Field(default=5)

    # ── Health Check ────────────────────────────────
    health_port: int = Field(default=8080)

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
