"""
Инициализация пакета services.
"""

from app.services.downloader import downloader
from app.services.redis_client import redis_client

__all__ = ["downloader", "redis_client"]
