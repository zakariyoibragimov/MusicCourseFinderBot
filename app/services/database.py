"""
Database service using SQLAlchemy with asyncpg
"""

import asyncpg
from sqlalchemy.ext.asyncio import (
    AsyncSession, create_async_engine, async_sessionmaker
)
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, JSON, Text, BigInteger, text, select, func, UniqueConstraint
from datetime import datetime
from app.utils.logger import logger

Base = declarative_base()


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, index=True)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    language = Column(String, default="ru")
    audio_bitrate = Column(String, default="192")
    video_resolution = Column(String, default="720")
    referred_by = Column(BigInteger, nullable=True)
    free_usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)


class Favorite(Base):
    """Favorites model"""
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "track_id", name="uq_favorites_user_track"),)
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, index=True)
    track_id = Column(String)
    title = Column(String)
    source = Column(String)  # youtube, soundcloud, etc
    url = Column(String)
    duration = Column(Integer)
    added_at = Column(DateTime, default=datetime.utcnow)


class History(Base):
    """History model"""
    __tablename__ = "history"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, index=True)
    track_id = Column(String)
    title = Column(String)
    source = Column(String)
    url = Column(String)
    duration = Column(Integer)
    action = Column(String)  # downloaded, listened, etc
    accessed_at = Column(DateTime, default=datetime.utcnow)


class Queue(Base):
    """Queue model"""
    __tablename__ = "queues"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, index=True)
    track_id = Column(String)
    title = Column(String)
    source = Column(String)
    url = Column(String)
    duration = Column(Integer)
    position = Column(Integer)
    added_at = Column(DateTime, default=datetime.utcnow)


class Referral(Base):
    """Referral tracking model"""
    __tablename__ = "referrals"
    
    id = Column(Integer, primary_key=True)
    referrer_id = Column(BigInteger, index=True, nullable=False)
    referred_id = Column(BigInteger, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class FileCache(Base):
    """File cache model"""
    __tablename__ = "file_cache"
    
    id = Column(Integer, primary_key=True)
    track_id = Column(String, unique=True, index=True)
    file_path = Column(String)
    file_size_mb = Column(Float)
    format = Column(String)  # mp3, mp4, etc
    quality = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)


class DatabaseService:
    """Database service for async operations"""
    
    def __init__(self, database_url: str):
        """Initialize database service"""
        self.database_url = database_url
        self.engine = None
        self.session_factory = None
    
    async def initialize(self) -> None:
        """Initialize database connection and create tables"""
        try:
            # Create async engine
            self.engine = create_async_engine(
                self.database_url,
                echo=False,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20
            )
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                for statement in [
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS language VARCHAR DEFAULT 'ru'",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS audio_bitrate VARCHAR DEFAULT '192'",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS video_resolution VARCHAR DEFAULT '720'",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS referred_by BIGINT",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS free_usage_count INTEGER DEFAULT 0",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_active TIMESTAMP DEFAULT NOW()",
                    "ALTER TABLE favorites ADD COLUMN IF NOT EXISTS source VARCHAR",
                    "ALTER TABLE favorites ADD COLUMN IF NOT EXISTS url VARCHAR",
                    "ALTER TABLE favorites ADD COLUMN IF NOT EXISTS duration INTEGER",
                    "ALTER TABLE favorites ADD COLUMN IF NOT EXISTS added_at TIMESTAMP DEFAULT NOW()",
                    "ALTER TABLE history ADD COLUMN IF NOT EXISTS source VARCHAR",
                    "ALTER TABLE history ADD COLUMN IF NOT EXISTS url VARCHAR",
                    "ALTER TABLE history ADD COLUMN IF NOT EXISTS duration INTEGER",
                    "ALTER TABLE history ADD COLUMN IF NOT EXISTS action VARCHAR DEFAULT 'listened'",
                    "ALTER TABLE history ADD COLUMN IF NOT EXISTS accessed_at TIMESTAMP DEFAULT NOW()",
                    "ALTER TABLE queues ADD COLUMN IF NOT EXISTS source VARCHAR",
                    "ALTER TABLE queues ADD COLUMN IF NOT EXISTS url VARCHAR",
                    "ALTER TABLE queues ADD COLUMN IF NOT EXISTS duration INTEGER",
                    "ALTER TABLE queues ADD COLUMN IF NOT EXISTS position INTEGER DEFAULT 1",
                    "ALTER TABLE queues ADD COLUMN IF NOT EXISTS added_at TIMESTAMP DEFAULT NOW()",
                    "ALTER TABLE users ALTER COLUMN user_id TYPE BIGINT",
                    "ALTER TABLE users ALTER COLUMN referred_by TYPE BIGINT",
                    "ALTER TABLE favorites ALTER COLUMN user_id TYPE BIGINT",
                    "ALTER TABLE history ALTER COLUMN user_id TYPE BIGINT",
                    "ALTER TABLE queues ALTER COLUMN user_id TYPE BIGINT",
                    "ALTER TABLE referrals ALTER COLUMN referrer_id TYPE BIGINT",
                    "ALTER TABLE referrals ALTER COLUMN referred_id TYPE BIGINT",
                    "ALTER TABLE favorites DROP CONSTRAINT IF EXISTS favorites_track_id_key",
                    "DROP INDEX IF EXISTS favorites_track_id_key",
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_favorites_user_track ON favorites (user_id, track_id)",
                ]:
                    try:
                        await conn.execute(text(statement))
                    except Exception:
                        pass
            
            logger.info("✓ Database initialized successfully")
        except Exception as e:
            logger.error(f"✗ Failed to initialize database: {e}")
            raise
    
    async def get_session(self) -> AsyncSession:
        """Get database session"""
        if not self.session_factory:
            raise RuntimeError("Database not initialized")
        return self.session_factory()

    @staticmethod
    def _track_payload(track: dict) -> dict:
        """Normalize track payload before saving to database."""
        track_id = str(track.get("id") or track.get("track_id") or track.get("url") or track.get("title") or "unknown")
        source = track.get("source", "youtube")
        url = track.get("url")
        if not url and source == "youtube" and track.get("id"):
            url = f"https://youtube.com/watch?v={track['id']}"

        duration = track.get("duration", 0)
        try:
            duration = int(duration or 0)
        except (TypeError, ValueError):
            duration = 0

        return {
            "track_id": track_id,
            "title": track.get("title", "Unknown"),
            "source": source,
            "url": url,
            "duration": duration,
        }

    async def ensure_user(
        self,
        user_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        language: str = "ru",
    ) -> None:
        """Ensure user exists in the database and update last active timestamp."""
        session = await self.get_session()
        async with session:
            result = await session.execute(select(User).where(User.user_id == user_id))
            db_user = result.scalar_one_or_none()
            if not db_user:
                db_user = User(
                    user_id=user_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    language=language,
                )
                session.add(db_user)
            else:
                db_user.username = username
                db_user.first_name = first_name
                db_user.last_name = last_name
                db_user.language = language or db_user.language

            db_user.last_active = datetime.utcnow()
            await session.commit()

    async def add_to_queue(self, user_id: int, track: dict) -> int:
        """Add track to user queue and return its position."""
        payload = self._track_payload(track)
        session = await self.get_session()
        async with session:
            max_position_result = await session.execute(
                select(func.max(Queue.position)).where(Queue.user_id == user_id)
            )
            next_position = (max_position_result.scalar() or 0) + 1
            session.add(Queue(user_id=user_id, position=next_position, **payload))
            await session.commit()
            return next_position

    async def get_user_queue(self, user_id: int, limit: int = 20) -> list[Queue]:
        """Return user queue ordered by position."""
        session = await self.get_session()
        async with session:
            result = await session.execute(
                select(Queue)
                .where(Queue.user_id == user_id)
                .order_by(Queue.position.asc(), Queue.added_at.asc())
                .limit(limit)
            )
            return list(result.scalars().all())

    async def add_to_favorites(self, user_id: int, track: dict) -> bool:
        """Add track to favorites. Returns False when it already exists."""
        payload = self._track_payload(track)
        session = await self.get_session()
        async with session:
            existing = await session.execute(
                select(Favorite).where(
                    Favorite.user_id == user_id,
                    Favorite.track_id == payload["track_id"],
                )
            )
            if existing.scalar_one_or_none():
                return False

            session.add(Favorite(user_id=user_id, **payload))
            await session.commit()
            return True

    async def get_user_favorites(self, user_id: int, limit: int = 20) -> list[Favorite]:
        """Return latest user favorites."""
        session = await self.get_session()
        async with session:
            result = await session.execute(
                select(Favorite)
                .where(Favorite.user_id == user_id)
                .order_by(Favorite.added_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())

    async def add_history_entry(self, user_id: int, track: dict, action: str = "listened") -> None:
        """Save history entry for a user."""
        payload = self._track_payload(track)
        session = await self.get_session()
        async with session:
            session.add(History(user_id=user_id, action=action, **payload))
            await session.commit()

    async def get_user_history(self, user_id: int, limit: int = 10) -> list[History]:
        """Return latest user history entries."""
        session = await self.get_session()
        async with session:
            result = await session.execute(
                select(History)
                .where(History.user_id == user_id)
                .order_by(History.accessed_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())

    async def get_free_usage_count(self, user_id: int) -> int:
        """Return the number of free music actions already used by the user."""
        session = await self.get_session()
        async with session:
            result = await session.execute(select(User).where(User.user_id == user_id))
            db_user = result.scalar_one_or_none()
            return int(db_user.free_usage_count or 0) if db_user else 0

    async def increment_free_usage_count(
        self,
        user_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        language: str = "ru",
    ) -> int:
        """Increment free music usage counter and return the updated value."""
        session = await self.get_session()
        async with session:
            result = await session.execute(select(User).where(User.user_id == user_id))
            db_user = result.scalar_one_or_none()
            if not db_user:
                db_user = User(
                    user_id=user_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    language=language,
                    free_usage_count=0,
                )
                session.add(db_user)

            db_user.username = username
            db_user.first_name = first_name
            db_user.last_name = last_name
            db_user.language = language or db_user.language
            db_user.free_usage_count = int(db_user.free_usage_count or 0) + 1
            db_user.last_active = datetime.utcnow()

            await session.commit()
            return int(db_user.free_usage_count)
    
    async def close(self) -> None:
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()
            logger.info("✓ Database connection closed")


# Global database service
db_service: DatabaseService = None
