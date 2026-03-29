"""
Сервис для работы с Redis.
"""

import redis.asyncio as redis
from typing import Optional, Any
from app.config import Config
from app.utils import logger
import json


class RedisClient:
    """Класс для управления Redis подключением."""
    
    def __init__(self):
        """Инициализирует Redis клиент."""
        self.redis: Optional[redis.Redis] = None
    
    async def initialize(self) -> None:
        """Инициализирует подключение к Redis."""
        try:
            self.redis = await redis.from_url(
                Config.REDIS_URL,
                encoding="utf8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
            )
            
            # Проверяем подключение
            await self.redis.ping()
            logger.info("✓ Redis инициализирован успешно")
        except Exception as e:
            logger.error(f"✗ Ошибка при инициализации Redis: {e}")
            raise
    
    async def close(self) -> None:
        """Закрывает подключение к Redis."""
        if self.redis:
            await self.redis.close()
            logger.info("✓ Redis подключение закрыто")
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Сохраняет значение в Redis.
        
        Args:
            key: Ключ
            value: Значение (будет преобразовано в JSON если нужно)
            ttl: TTL в секундах
            
        Returns:
            True если успешно
        """
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            if ttl:
                await self.redis.setex(key, ttl, value)
            else:
                await self.redis.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении в Redis {key}: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Получает значение из Redis.
        
        Args:
            key: Ключ
            
        Returns:
            Значение или None
        """
        try:
            value = await self.redis.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении из Redis {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Удаляет значение из Redis."""
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении из Redis {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Проверяет наличие ключа."""
        try:
            return await self.redis.exists(key) > 0
        except Exception:
            return False
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Увеличивает значение счетчика."""
        try:
            return await self.redis.incrby(key, amount)
        except Exception as e:
            logger.error(f"Ошибка при увеличении счетчика {key}: {e}")
            return 0
    
    async def clear_pattern(self, pattern: str) -> int:
        """Удаляет все ключи по паттерну."""
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Ошибка при удалении паттерна {pattern}: {e}")
            return 0


# Глобальный объект Redis
redis_client = RedisClient()
