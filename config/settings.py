import os
import secrets
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = "sqlite:///./oneway_sentinel.db"
    DATABASE_WAL_MODE: bool = True

    CAPTURE_INTERFACE: str = "eth0"
    PROMISCUOUS_MODE: bool = True

    FLOW_WINDOW_SECONDS: float = 5.0
    ALERT_THRESHOLD: int = 40
    CRITICAL_THRESHOLD: int = 80
    DEDUP_WINDOW_SECONDS: float = 60.0

    WEIGHT_SUPERVISED_RF: float = 0.60
    WEIGHT_UNSUPERVISED_IF: float = 0.40

    THREAT_INTEL_DIR: str = "./data/threat_intel"
    MAXMIND_GEOIP_DB: str = "./data/threat_intel/GeoLite2-City.mmdb"

    # Authentication & Security Settings (P2 / Toggleable)
    ENABLE_AUTH: bool = False
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
