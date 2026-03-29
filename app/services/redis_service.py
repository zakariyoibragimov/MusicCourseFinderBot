"""
Redis service for caching and rate limiting
"""

import json
import redis.asyncio as redis
from typing import Any, Optional
from app.utils.logger import logger


class RedisService:
    """Redis service for caching operations"""
    
    def __init__(self, redis_url: str):
        """Initialize Redis service"""
        self.redis_url = redis_url
        self.client: Optional[redis.Redis] = None

    def is_available(self) -> bool:
        """Return True if Redis client is initialized and ready."""
        return self.client is not None
    
    async def initialize(self) -> None:
        """Initialize Redis connection"""
        try:
            self.client = await redis.from_url(self.redis_url, decode_responses=True)
            # Test connection
            await self.client.ping()
            logger.info("✓ Redis connected successfully")
        except Exception as e:
            logger.error(f"✗ Failed to initialize Redis: {e}")
            raise
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.client:
            return None
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value) if value.startswith(('{', '[')) else value
            return None
        except Exception as e:
            logger.error(f"Error getting key {key} from Redis: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 600) -> bool:
        """Set value in cache with TTL"""
        if not self.client:
            return False
        try:
            json_value = json.dumps(value) if isinstance(value, (dict, list)) else value
            await self.client.setex(key, ttl, json_value)
            return True
        except Exception as e:
            logger.error(f"Error setting key {key} in Redis: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.client:
            return False
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting key {key} from Redis: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.client:
            return False
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking key {key} in Redis: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        if not self.client:
            return 0
        try:
            return await self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Error incrementing key {key} in Redis: {e}")
            return 0
    
    async def get_ttl(self, key: str) -> int:
        """Get remaining TTL in seconds (-1 if no expiry, -2 if key doesn't exist)"""
        if not self.client:
            return -2
        try:
            return await self.client.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL for key {key} from Redis: {e}")
            return -2
    
    async def flush_db(self) -> bool:
        """Flush entire database (use with caution!)"""
        if not self.client:
            return False
        try:
            await self.client.flushdb()
            logger.warning("Redis database flushed")
            return True
        except Exception as e:
            logger.error(f"Error flushing Redis database: {e}")
            return False
    
    async def close(self) -> None:
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("✓ Redis connection closed")


# Global Redis service instance
redis_service: Optional[RedisService] = None
