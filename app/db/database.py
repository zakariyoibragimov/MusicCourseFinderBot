"""
Совместимый слой для работы с PostgreSQL базой данных.
"""

from contextlib import asynccontextmanager
from app.config import Config
from app.services.database import DatabaseService
from app.utils import logger


class Database(DatabaseService):
    """Совместимый wrapper над основным DatabaseService."""

    def __init__(self):
        super().__init__(Config.DATABASE_URL)
    
    async def initialize(self) -> None:
        await super().initialize()
        logger.info("✓ Совместимый DB wrapper инициализирован")
    
    async def close(self) -> None:
        await super().close()
        logger.info("✓ Совместимый DB wrapper закрыт")
    
    @asynccontextmanager
    async def get_session(self):
        """
        Возвращает сессию БД.
        
        Yields:
            AsyncSession объект
        """
        session = await super().get_session()
        async with session:
            yield session


# Глобальный объект БД
db = Database()
