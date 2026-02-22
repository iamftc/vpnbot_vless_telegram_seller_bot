"""
Конфигурация приложения с валидацией через Pydantic
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, validator
import os


class Settings(BaseSettings):
    # Bot
    BOT_TOKEN: str = Field(..., description="Telegram Bot Token")
    BOT_WEBHOOK_URL: str | None = Field(None, description="Webhook URL")
    BOT_WEBHOOK_SECRET: str | None = Field(None, description="Webhook Secret")
    
    # Admin
    ADMIN_IDS: str = Field(..., description="Comma-separated admin IDs")
    
    # 3x-ui
    XUI_BASE_URL: str = Field(..., description="3x-ui Panel URL")
    XUI_USERNAME: str = Field(..., description="3x-ui Username")
    XUI_PASSWORD: str = Field(..., description="3x-ui Password")
    DEFAULT_SUB_DOMAIN: str = Field("your.domain.com", description="Subscription Domain")
    
    # CryptoBot
    CRYPTOBOT_TOKEN: str = Field(..., description="CryptoBot Token")
    CRYPTOBOT_NETWORK: str = Field("mainnet", description="CryptoBot Network")
    
    # Database
    DATABASE_URL: str = Field(..., description="PostgreSQL Connection String")
    DATABASE_POOL_SIZE: int = Field(20, ge=5, le=100)
    DATABASE_MAX_OVERFLOW: int = Field(10, ge=0, le=50)
    
    # Redis
    REDIS_URL: str = Field("redis://localhost:6379/0", description="Redis URL")
    REDIS_CACHE_TTL: int = Field(3600, ge=60, le=86400)
    
    # Security
    SECRET_KEY: str = Field(..., min_length=32)
    ENCRYPTION_KEY: str = Field(..., min_length=32)
    
    # Logging
    LOG_LEVEL: str = Field("INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    LOG_FILE: str = Field("logs/bot.log")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(60, ge=10, le=1000)
    RATE_LIMIT_BURST: int = Field(10, ge=1, le=100)
    
    # Pricing
    DEFAULT_STARS_7_DAYS: int = Field(10, ge=1)
    DEFAULT_STARS_30_DAYS: int = Field(11, ge=1)
    DEFAULT_CRYPTO_7_DAYS: float = Field(1.0, ge=0.1)
    DEFAULT_CRYPTO_30_DAYS: float = Field(3.0, ge=0.1)
    
    # Maintenance
    MAINTENANCE_MODE: bool = Field(False)
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @validator('ADMIN_IDS')
    def parse_admin_ids(cls, v):
        return [int(x.strip()) for x in v.split(',') if x.strip().isdigit()]
    
    @property
    def admin_ids_set(self) -> set[int]:
        return set(self.ADMIN_IDS)


settings = Settings()