# 👨‍💻 Development Guide

Complete guide for developers working on the music bot project.

## Table of Contents

1. [Project Structure](#project-structure)
2. [Development Environment](#development-environment)
3. [Code Style & Standards](#code-style--standards)
4. [Adding Features](#adding-features)
5. [Testing](#testing)
6. [Debugging](#debugging)
7. [Git Workflow](#git-workflow)
8. [Common Tasks](#common-tasks)

---

## Project Structure

```
music-bot/
├── app/
│   ├── __init__.py
│   ├── config.py                 # Configuration management
│   ├── main.py                   # Application entry point
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── commands.py           # Bot commands (/start, /search, etc)
│   │   ├── search.py             # Search and inline search
│   │   ├── download.py           # Download quality selection
│   │   ├── playback.py           # Playback controls
│   │   └── voice_chat.py         # Voice channel integration
│   ├── services/
│   │   ├── __init__.py
│   │   ├── database.py           # PostgreSQL + SQLAlchemy ORM
│   │   ├── redis_service.py      # Redis caching
│   │   ├── downloader.py         # Media download and search
│   │   └── cloud_storage/
│   │       ├── google_drive.py   # Google Drive integration
│   │       └── dropbox.py        # Dropbox integration
│   └── utils/
│       ├── __init__.py
│       ├── logger.py             # Logging configuration
│       ├── rate_limiter.py       # Rate limiting
│       └── helpers.py            # Utility functions
├── migrations/                    # Alembic database migrations
├── tests/
│   ├── __init__.py
│   ├── test_handlers.py
│   ├── test_services.py
│   └── test_utils.py
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Container image
├── docker-compose.yml            # Multi-container orchestration
├── .env.example                  # Environment template
├── init_db.py                    # Database initialization
├── ARCHITECTURE.md               # Architecture documentation
├── QUICKSTART.md                 # Quick start guide
├── DEPLOYMENT.md                 # Production deployment
└── README.md                     # Main documentation
```

---

## Development Environment

### 1. Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- FFmpeg
- Git
- IDE: VS Code or PyCharm

### 2. Setup Development Environment

```bash
# Clone repository
git clone <repo-url>
cd music-bot

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Install development dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt  # if exists

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

### 3. Database Setup

```bash
# Start PostgreSQL (if not running)
# Ubuntu: sudo systemctl start postgresql
# macOS: brew services start postgresql

# Create development database
createdb music_bot_dev

# Initialize tables
python init_db.py
```

### 4. Redis Setup

```bash
# Start Redis
# Ubuntu: sudo systemctl start redis-server
# macOS: brew services start redis
redis-server

# Verify connection
redis-cli ping  # Should return "PONG"
```

### 5. Environment Configuration

```bash
# Copy and edit .env
cp .env.example .env
nano .env

# Required for development:
BOT_TOKEN=your_test_bot_token
ADMIN_ID=your_telegram_id
DB_HOST=localhost
REDIS_HOST=localhost
LOG_LEVEL=DEBUG
```

### 6. Run Development Server

```bash
# With auto-reload (requires library)
# pip install auto-reload-on-edit
watchmedo auto-restart -d app -p '*.py' -- python -m app.main

# Or simple run
python -m app.main
```

---

## Code Style & Standards

### Python Code Standards

**Follow PEP 8:**
```bash
# Install and run linter
pip install pylint flake8
pylint app/
flake8 app/

# Auto-format code
pip install black
black app/
```

**Type Hints Required:**
```python
# ✅ Good
async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query: str = " ".join(context.args)
    results: list[dict] = await downloader.search(query)

# ❌ Bad
async def search_handler(update, context):
    query = " ".join(context.args)
    results = await downloader.search(query)
```

**Docstrings for All Functions:**
```python
async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /search command.
    
    Args:
        update: Telegram update object
        context: CallbackContext with user data
        
    Returns:
        None
        
    Raises:
        ValueError: If query is empty
    """
    # Implementation
```

**Async/Await Only:**
```python
# ✅ Good - always async
async def download_file(url: str) -> bytes:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.read()

# ❌ Bad - blocks event loop
def download_file(url: str) -> bytes:
    response = requests.get(url)
    return response.content
```

### Naming Conventions

```python
# Constants - UPPER_CASE
MAX_FILE_SIZE_MB = 50
CACHE_TTL_SECONDS = 600

# Classes - PascalCase
class MediaDownloader:
    pass

class DatabaseService:
    pass

# Functions/Methods - snake_case
async def search_tracks(query: str) -> list:
    pass

async def download_audio(url: str) -> bytes:
    pass

# Private methods - prefix with _
async def _create_progress_hook(callback: Callable) -> Callable:
    pass
```

### Logging Standards

```python
from app.utils.logger import logger

# Info level - normal operations
logger.info(f"User {user_id} searched for: {query}")

# Debug level - detailed debug info
logger.debug(f"Cache key: {cache_key}, TTL: {ttl}")

# Warning level - non-critical issues
logger.warning(f"Cache size exceeds limit: {size}GB")

# Error level - exceptions
logger.error(f"Database connection failed: {str(e)}")

# Never use print()
# ❌ print("Debug info")  # Bad - goes to stdout
# ✅ logger.debug("Debug info")  # Good - goes to log file
```

### Error Handling

```python
# Always catch and log specific exceptions
async def download_audio(self, url: str) -> str:
    try:
        # Download logic
        return file_path
    except FileNotFoundError as e:
        logger.error(f"File not found: {str(e)}")
        raise ValueError(f"Cannot download: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during download: {str(e)}")
        raise RuntimeError("Download failed unexpectedly") from e
```

---

## Adding Features

### 1. Add New Command Handler

**Example: Add `/save` command**

```python
# In app/handlers/commands.py

async def save_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /save command - save current track to favorites"""
    
    user_id = update.effective_user.id
    
    # Check if track is provided
    if not context.args:
        await update.message.reply_text("❌ No track to save")
        return
    
    try:
        track_id = context.args[0]
        
        # Get database service
        db = context.bot_data.get("database_service")
        
        # TODO: Query database to add to favorites
        # await db.add_favorite(user_id, track_id)
        
        await update.message.reply_text("✅ Track saved to favorites")
        logger.info(f"Favorite added: user={user_id}, track={track_id}")
        
    except Exception as e:
        logger.error(f"Save command error: {str(e)}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


# In app/main.py, register handler:
from app.handlers.commands import save_handler

def setup_handlers(application: Application) -> None:
    # ... existing handlers
    
    # Add new handler
    application.add_handler(CommandHandler("save", save_handler))
    
    logger.info("✅ All handlers registered")
```

### 2. Add New Service

**Example: Spotify integration**

```python
# Create app/services/spotify_service.py

from spotipy.oauth2 import SpotifyClientCredentials
import spotipy

class SpotifyService:
    """Spotify music search and metadata"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._spotify = None
    
    async def initialize(self) -> None:
        """Initialize Spotify client"""
        auth_manager = SpotifyClientCredentials(
            client_id=self.client_id,
            client_secret=self.client_secret
        )
        self._spotify = spotipy.Spotify(auth_manager=auth_manager)
        logger.info("✅ Spotify client initialized")
    
    async def search(self, query: str, limit: int = 5) -> list:
        """Search for tracks on Spotify"""
        try:
            results = self._spotify.search(q=query, type='track', limit=limit)
            
            tracks = []
            for item in results['tracks']['items']:
                tracks.append({
                    'id': item['id'],
                    'title': item['name'],
                    'artist': item['artists'][0]['name'],
                    'duration': item['duration_ms'] // 1000,
                    'source': 'spotify',
                    'url': item['external_urls']['spotify'],
                })
            
            return tracks
        
        except Exception as e:
            logger.error(f"Spotify search error: {str(e)}")
            return []


# In app/main.py:
async def post_init(application: Application) -> None:
    config = Config()
    
    # Initialize services
    # ... existing services
    
    # Add Spotify service
    spotify = SpotifyService(
        client_id=config.spotify_client_id,
        client_secret=config.spotify_client_secret
    )
    await spotify.initialize()
    application.bot_data["spotify"] = spotify
```

### 3. Add Database Model

**Example: Add `Playlist` model**

```python
# In app/services/database.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Playlist(Base):
    """User created playlists"""
    __tablename__ = 'playlists'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000))
    is_public = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    tracks = relationship("PlaylistTrack", back_populates="playlist")
    user = relationship("User")


class PlaylistTrack(Base):
    """Tracks in playlists"""
    __tablename__ = 'playlist_tracks'
    
    id = Column(Integer, primary_key=True)
    playlist_id = Column(Integer, ForeignKey('playlists.id'))
    track_id = Column(String(255), nullable=False)
    title = Column(String(255))
    source = Column(String(50))
    url = Column(String(1000))
    position = Column(Integer)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    playlist = relationship("Playlist", back_populates="tracks")


# Initialize database will create new tables
# Run: python init_db.py
```

---

## Testing

### Unit Tests

```python
# tests/test_services.py

import pytest
import asyncio
from app.services.downloader import MediaDownloader


@pytest.fixture
async def downloader():
    """Create downloader instance"""
    return MediaDownloader()


@pytest.mark.asyncio
async def test_search(downloader):
    """Test music search"""
    results = await downloader.search("Never Gonna Give You Up", source="youtube", limit=5)
    
    assert len(results) > 0
    assert results[0]['title']
    assert results[0]['duration'] > 0
    assert results[0]['source'] == 'youtube'


@pytest.mark.asyncio
async def test_invalid_search(downloader):
    """Test search with invalid query"""
    results = await downloader.search("", source="youtube")
    
    # Should return empty list
    assert results == []


# Run tests
# pytest tests/ -v
# pytest tests/test_services.py::test_search -v
```

### Integration Tests

```python
# tests/test_handlers.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram import Update, User, Chat, Message
from app.handlers.commands import search_handler


@pytest.mark.asyncio
async def test_search_handler():
    """Test /search command handler"""
    
    # Mock Telegram objects
    update = AsyncMock(spec=Update)
    update.effective_user.id = 12345
    update.message.reply_text = AsyncMock()
    
    context = MagicMock()
    context.bot_data = {"downloader": AsyncMock()}
    context.args = ["test", "query"]
    
    # Call handler
    await search_handler(update, context)
    
    # Verify response
    update.message.reply_text.assert_called_once()
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_services.py::test_search -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

---

## Debugging

### Logging

```python
# By default, logs go to:
# - logs/bot.log (rotating file handler)
# - Console output

# Change log level
LOG_LEVEL=DEBUG python -m app.main

# View logs
tail -f logs/bot.log

# Search logs
grep "ERROR" logs/bot.log
grep "user_id=12345" logs/bot.log
```

### Debug Database Queries

```python
# In app/config.py
# Set echo=True to see all SQL queries

create_async_engine(
    db_url,
    echo=True,  # Print all SQL statements
    pool_size=20,
    max_overflow=10,
)
```

### Debug Async Operations

```python
# Use asyncio debugging
import asyncio

asyncio.run(main(), debug=True)

# Or in event loop
import logging
logging.basicConfig(level=logging.DEBUG)
asyncio.get_event_loop().set_debug(True)
```

### Browser Dev Tools

For webhook debugging:

```bash
# Use ngrok for local testing
ngrok http 8000

# Get URL like: https://7e6b-1-2-3-4.ngrok.io

# Telegram will send webhook to: https://7e6b-1-2-3-4.ngrok.io/webhook/
```

---

## Git Workflow

### Branching

```bash
# Create feature branch
git checkout -b feature/new-feature

# Create bugfix branch
git checkout -b bugfix/issue-description

# Create release branch
git checkout -b release/1.0.0

# Push branch
git push -u origin feature/new-feature
```

### Commits

```bash
# Good commit messages
git commit -m "Add Spotify search integration"
git commit -m "Fix rate limiter concurrent request bug"
git commit -m "Improve FFmpeg video conversion speed"

# Format: [type]: [description]
# Types: feat, fix, docs, style, refactor, test, chore
```

### Pull Requests

```bash
# Before creating PR:
1. Ensure all tests pass: pytest tests/
2. Run linter: pylint app/
3. Format code: black app/
4. Update documentation
5. Squash commits if needed

# Create PR on GitHub with:
- Description of changes
- Related issues
- Testing instructions
```

---

## Common Tasks

### Update Dependencies

```bash
# Show outdated packages
pip list --outdated

# Update specific package
pip install --upgrade python-telegram-bot

# Update all packages
pip install --upgrade -r requirements.txt

# Freeze current versions
pip freeze > requirements.txt
```

### Create Database Migration

```bash
# With Alembic (install: pip install alembic)
alembic init migrations

# Edit migration config in alembic.ini

# Create migration
alembic revision --autogenerate -m "Add playlist table"

# Apply migration
alembic upgrade head

# Downgrade (if needed)
alembic downgrade -1
```

### Clear Cache

```bash
# Via database
python -c "
from app.utils.helpers import clean_cache
import asyncio
asyncio.run(clean_cache(max_age_days=7, max_size_gb=50))
"

# Via command
# /clear_cache (admin only)
```

### Monitor Bot Performance

```bash
# CPU and memory usage
top -p $(pgrep -f "python -m app.main")

# Network usage
iftop

# Database connections
psql -c "SELECT count(*) FROM pg_stat_activity;"

# Redis memory
redis-cli info memory
```

### Create Development Webhook

```bash
# Using ngrok
ngrok http 8000

# Set webhook
curl -F "url=https://abcd-1.ngrok.io/webhook/" \
     -F "allowed_updates=message,callback_query,inline_query" \
     "https://api.telegram.org/bot<TOKEN>/setWebhook"

# Remove webhook
curl "https://api.telegram.org/bot<TOKEN>/deleteWebhook"
```

---

## Best Practices

### ✅ Do
- Write type hints for all functions
- Use async/await for all I/O operations
- Log important operations at INFO level
- Test your changes before committing
- Use meaningful variable names
- Handle exceptions properly
- Cache expensive operations
- Rate limit user requests

### ❌ Don't
- Use synchronous libraries (use aiohttp instead of requests)
- Hardcode credentials (use .env)
- Print to stdout (use logger)
- Leave TODOs without context
- Make blocking calls in async functions
- Ignore exceptions silently
- Commit to main branch directly
- Leave debug code in production

---

## Performance Tips

### Database
- Use indexes on frequently queried columns
- Connection pooling (already configured)
- Batch operations when possible
- Use LIMIT clause for large result sets

### Redis
- Set appropriate TTL values
- Monitor memory usage
- Use pipeline for batch commands
- Compress large values if needed

### Downloads
- Limit concurrent downloads (semaphore)
- Use appropriate bitrate/resolution
- Cache frequently downloaded files
- Clean old cache periodically

### Telegram API
- Use rate limiting per user
- Cache search results
- Batch message edits
- Use inline keyboards for navigation

---

**Happy developing! 🚀**
