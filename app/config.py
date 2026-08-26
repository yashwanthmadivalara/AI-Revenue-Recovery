import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Information
    PROJECT_NAME: str = "AI Revenue Recovery System"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    SECRET_KEY: str = "revenue_recovery_secret_key_12345"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./revenue_recovery.db"
    REDIS_URL: Optional[str] = None

    # LLM Settings
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.2

    # Payment Gateway Credentials (Optional / Mockable)
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None
    CHARGEBEE_API_KEY: Optional[str] = None

    # Communication Credentials (Optional / Mockable)
    SENDGRID_API_KEY: Optional[str] = None
    RESEND_API_KEY: Optional[str] = None
    FROM_EMAIL: str = "billing@recovery-ai.internal"
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = "+15005550006"
    VAPI_API_KEY: Optional[str] = None
    VAPI_ASSISTANT_ID: Optional[str] = None

    # Compliance & Guardrails Policy Defaults
    MAX_CONTACT_ATTEMPTS_PER_WEEK: int = 3
    ENABLE_DISPUTE_KILLSWITCH: bool = True
    ENABLE_QUIET_HOURS: bool = True
    QUIET_HOURS_START_UTC: int = 22  # 10 PM
    QUIET_HOURS_END_UTC: int = 7     # 7 AM
    HIGH_VALUE_THRESHOLD_USD: float = 5000.00
    PROMISE_TO_PAY_GRACE_DAYS: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
