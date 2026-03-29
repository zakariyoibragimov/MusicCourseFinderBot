"""
Configuration module for Telegram music bot
Reads environment variables and provides global settings
"""

import os
from typing import Optional, List
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Config:
    """
    Application settings from environment variables
    """
    
    # Telegram Bot
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))
    TELEGRAM_CONNECT_TIMEOUT: float = float(os.getenv("TELEGRAM_CONNECT_TIMEOUT", "30"))
    TELEGRAM_READ_TIMEOUT: float = float(os.getenv("TELEGRAM_READ_TIMEOUT", "30"))
    TELEGRAM_WRITE_TIMEOUT: float = float(os.getenv("TELEGRAM_WRITE_TIMEOUT", "30"))
    TELEGRAM_POOL_TIMEOUT: float = float(os.getenv("TELEGRAM_POOL_TIMEOUT", "10"))
    TELEGRAM_MEDIA_WRITE_TIMEOUT: float = float(os.getenv("TELEGRAM_MEDIA_WRITE_TIMEOUT", "60"))
    TELEGRAM_BOOTSTRAP_RETRIES: int = int(os.getenv("TELEGRAM_BOOTSTRAP_RETRIES", "3"))
    TELEGRAM_USE_ENV_PROXY: bool = os.getenv("TELEGRAM_USE_ENV_PROXY", "false").lower() == "true"
    TELEGRAM_PROXY_URL: Optional[str] = os.getenv("TELEGRAM_PROXY_URL", None)
    REQUIRED_CHANNEL_USERNAME: str = os.getenv("REQUIRED_CHANNEL_USERNAME", "@TjMusik")
    FREE_MUSIC_REQUEST_LIMIT: int = int(os.getenv("FREE_MUSIC_REQUEST_LIMIT", "3"))
    
    # Database - PostgreSQL
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "music_bot")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "password")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    
    # Redis
    REDIS_ENABLED: bool = os.getenv("REDIS_ENABLED", "true").lower() == "true"
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD", None)
    REDIS_URL: str = os.getenv(
        "REDIS_URL",
        f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}" if REDIS_PASSWORD 
        else f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    )
    
    # Cloud Storage (заглушки для подключения)
    GOOGLE_DRIVE_ENABLED: bool = os.getenv("GOOGLE_DRIVE_ENABLED", "false").lower() == "true"
    GOOGLE_DRIVE_CREDENTIALS: Optional[str] = os.getenv("GOOGLE_DRIVE_CREDENTIALS", None)
    GOOGLE_DRIVE_FOLDER_ID: Optional[str] = os.getenv("GOOGLE_DRIVE_FOLDER_ID", None)
    
    DROPBOX_ENABLED: bool = os.getenv("DROPBOX_ENABLED", "false").lower() == "true"
    DROPBOX_TOKEN: Optional[str] = os.getenv("DROPBOX_TOKEN", None)
    
    SPOTIFY_CLIENT_ID: Optional[str] = os.getenv("SPOTIFY_CLIENT_ID", None)
    SPOTIFY_CLIENT_SECRET: Optional[str] = os.getenv("SPOTIFY_CLIENT_SECRET", None)
    
    # FFmpeg path
    FFMPEG_PATH: str = os.getenv("FFMPEG_PATH", "ffmpeg")
    
    # Application settings
    APP_NAME: str = os.getenv("APP_NAME", "Finder Music Bot")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Download settings
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    PREMIUM_FILE_SIZE_MB: int = int(os.getenv("PREMIUM_FILE_SIZE_MB", "2000"))
    DOWNLOAD_TIMEOUT: int = int(os.getenv("DOWNLOAD_TIMEOUT", "300"))
    MAX_CONCURRENT_DOWNLOADS: int = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "3"))
    
    # Cache settings
    CACHE_DIR: str = os.getenv("CACHE_DIR", "./cache")
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "600"))  # 10 minutes for search
    CACHE_FILE_TTL: int = int(os.getenv("CACHE_FILE_TTL", "604800"))  # 7 days for files
    CACHE_MAX_SIZE_GB: int = int(os.getenv("CACHE_MAX_SIZE_GB", "10"))
    
    # Search settings
    SEARCH_RESULTS_PER_PAGE: int = 5
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "5"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    
    # Audio quality options (kbps)
    SUPPORTED_AUDIO_BITRATES: List[str] = os.getenv(
        "SUPPORTED_AUDIO_BITRATES", "96,128,192,320"
    ).split(",")
    DEFAULT_AUDIO_BITRATE: str = os.getenv("DEFAULT_AUDIO_BITRATE", "192")
    
    # Video quality options (p)
    SUPPORTED_VIDEO_RESOLUTIONS: List[str] = os.getenv(
        "SUPPORTED_VIDEO_RESOLUTIONS", "480,720,1080"
    ).split(",")
    DEFAULT_VIDEO_RESOLUTION: str = os.getenv("DEFAULT_VIDEO_RESOLUTION", "720")
    
    # Supported sources
    SUPPORTED_SOURCES: List[str] = ["youtube", "soundcloud", "vimeo", "tiktok", "instagram", "spotify"]
    
    # Logging
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/bot.log")
    
    # Paths
    DOWNLOADS_DIR: str = "cache/downloads"
    
    @classmethod
    def validate(cls) -> bool:
        """Проверяет обязательные параметры конфигурации."""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не установлен")
        if not cls.ADMIN_ID or cls.ADMIN_ID == 0:
            raise ValueError("ADMIN_ID не установлен")
        if not cls.REQUIRED_CHANNEL_USERNAME:
            raise ValueError("REQUIRED_CHANNEL_USERNAME не установлен")
        # Create required directories
        Path(cls.CACHE_DIR).mkdir(parents=True, exist_ok=True)
        Path(cls.DOWNLOADS_DIR).mkdir(parents=True, exist_ok=True)
        Path("logs").mkdir(parents=True, exist_ok=True)
        return True
