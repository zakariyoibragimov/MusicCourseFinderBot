"""
Модели базы данных для работы с пользователями, треками и историей.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, BigInteger, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """Модель пользователя бота."""
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True)  # Telegram ID
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    language = Column(String(10), default="ru")
    audio_bitrate = Column(String(10), default="192")
    video_resolution = Column(String(10), default="720")
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    history = relationship("History", back_populates="user", cascade="all, delete-orphan")
    queue = relationship("Queue", back_populates="user", cascade="all, delete-orphan")


class Track(Base):
    """Модель трека (песни/видео)."""
    __tablename__ = "tracks"
    
    id = Column(String(255), primary_key=True)  # YouTube ID или другой ID
    title = Column(String(500), nullable=False)
    artist = Column(String(255), nullable=True)
    duration = Column(Integer)  # в секундах
    url = Column(String(500), unique=True)
    source = Column(String(50))  # youtube, soundcloud, spotify, etc.
    thumbnail_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Favorite(Base):
    """Модель избранного пользователя."""
    __tablename__ = "favorites"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    track_id = Column(String(255), ForeignKey("tracks.id"), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="favorites")
    track = relationship("Track")


class History(Base):
    """Модель истории загрузок/прослушиваний."""
    __tablename__ = "history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    track_id = Column(String(255), ForeignKey("tracks.id"), nullable=False)
    action = Column(String(50))  # download, listened, searched
    downloaded_size = Column(Float, nullable=True)  # MB
    downloaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="history")
    track = relationship("Track")


class Queue(Base):
    """Модель очереди воспроизведения."""
    __tablename__ = "queue"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    track_id = Column(String(255), ForeignKey("tracks.id"), nullable=False)
    position = Column(Integer, nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="queue")
    track = relationship("Track")


class PopularTrack(Base):
    """Модель популярных треков."""
    __tablename__ = "popular_tracks"
    
    id = Column(String(255), primary_key=True)  # track ID
    track_id = Column(String(255), ForeignKey("tracks.id"), nullable=False)
    rank = Column(Integer)
    downloads_count = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    track = relationship("Track")


class FileCache(Base):
    """Модель кэша загруженных файлов."""
    __tablename__ = "file_cache"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    track_id = Column(String(255), ForeignKey("tracks.id"), nullable=False)
    format = Column(String(20))  # mp3, mp4
    file_path = Column(String(500), unique=True)
    file_size = Column(Float)  # MB
    created_at = Column(DateTime, default=datetime.utcnow)
    accessed_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    track = relationship("Track")
