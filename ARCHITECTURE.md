# 🏗️ Architecture Documentation

Complete technical architecture of the Telegram Music Bot.

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         TELEGRAM API                            │
└──────────────┬──────────────────────────────────────────────────┘
               │ Messages, callbacks, inline queries
               │
┌──────────────▼──────────────────────────────────────────────────┐
│                    PYTHON-TELEGRAM-BOT v20.7                    │
│              (Async framework, handlers registry)               │
└──────────────┬──────────────────────────────────────────────────┘
               │
     ┌─────────┴──────────┬────────────┬──────────────┐
     │                    │            │              │
┌────▼────┐  ┌────────────▼──┐ ┌──────▼──────┐  ┌───▼─────────┐
│ Command │  │   Handlers    │ │   Services  │  │  Utilities  │
│Handlers │  │                │ │             │  │             │
├─────────┤  ├────────────────┤ ├─────────────┤  ├─────────────┤
│ /start  │  │ - commands.py  │ │ - database  │  │ - logger    │
│ /search │  │ - download.py  │ │ - redis     │  │ - helpers   │
│ /help   │  │ - search.py    │ │ - downloader│  │ - rate_lim  │
│ /play   │  │ - playback.py  │ │ - cloud_*   │  │             │
│ etc.    │  │ - voice_chat.py│ │ - spotify   │  │             │
└────┬────┘  └────────────────┘ └─────────────┘  └─────────────┘
     │                │                │
     │                └────┬───────────┘
     │                     │
     └──────────┬──────────┴──────────┬──────────────┐
                │                     │              │
        ┌───────▼──────┐   ┌──────────▼──┐   ┌──────▼────────┐
        │              │   │             │   │               │
    PostgreSQL     Redis         Files       External APIs
   (Users,      (Search   (MP3/MP4 cache) YouTube, Spotify
  Favorites,   Results,              SoundCloud, cloud
   History,    Rate Limits)           storage, etc
   Queue)
```

---

## Component Architecture

### 1. **Application Layer** (`app/main.py`)

**Responsibilities:**
- Bot initialization and configuration
- Handler registration
- Service lifecycle management (startup/shutdown)
- Application entry point

**Key Classes:**
- `Application` - Main bot application from python-telegram-bot

**Lifecycle:**
```
main()
  ├── Load config
  ├── Validate config
  ├── Create Application
  ├── post_init() - Initialize services
  │   ├── DatabaseService
  │   └── RedisService
  ├── Register handlers
  ├── Start polling
  └── post_stop() - Cleanup
      ├── Close database
      └── Close Redis
```

---

### 2. **Configuration Layer** (`app/config.py`)

**Responsibilities:**
- Environment variable management
- Configuration validation
- Connection URL generation
- Directory auto-creation

**Key Components:**

```python
class Config:
    # Telegram
    bot_token: str
    admin_id: int
    
    # Database
    db_user: str
    db_password: str
    db_name: str
    db_host: str = "localhost"
    db_port: int = 5432
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    
    # Media quality
    default_audio_bitrate: str
    default_video_resolution: str
    
    # File limits
    max_file_size_mb: int
    premium_file_size_mb: int
```

**Features:**
- Type validation with Pydantic
- Directory auto-creation for logs, cache
- Secure password handling
- Database URL generation for SQLAlchemy

---

### 3. **Handler Layer** (`app/handlers/`)

Processes user interactions and delegates to services.

#### 3.1 **Command Handlers** (`commands.py`)
- `/start` - Main menu
- `/help` - Documentation
- `/search <query>` - Music search
- `/settings` - User preferences
- `/queue` - Playback queue
- `/history` - Download history
- `/favorites` - Saved tracks
- `/popular` - Trending tracks
- `/play` - Start playback
- `/skip` - Next track
- `/add <number>` - Add to queue
- `/clear_cache` - Cache management (admin only)

**Decorator Pattern:**
```python
@admin_only
async def clear_cache_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Only ADMIN_ID can call"""
    pass
```

#### 3.2 **Search Handlers** (`search.py`)
- Inline search: `@botname query`
- Search results pagination
- Track action buttons
- Caching of search results

**Flow:**
```
User types @botname "query"
    ↓
inline_search_handler()
    ├── Check Redis cache
    ├── If miss: MediaDownloader.search()
    ├── Cache result
    └── Return 5 InlineQueryResults
```

#### 3.3 **Download Handlers** (`download.py`)
- Quality selection (MP3/MP4)
- Download progress tracking
- File size validation
- Cache management

**Quality Selection:**
```
User clicks "MP3"
    ↓
Show bitrate keyboard: [96, 128, 192, 320] kbps
    ↓
User selects bitrate
    ↓
MediaDownloader.download_audio()
    ├── Download from source
    ├── Convert to MP3 with bitrate
    └── Send to user
```

#### 3.4 **Playback Handlers** (`playback.py`)
- `/play` - Start playback
- `/skip` - Next track
- `/pause` - Pause playback
- `/resume` - Resume playback
- Queue management

#### 3.5 **Voice Chat Handlers** (`voice_chat.py`)
- `/join` - Join voice channel
- `/play` - Stream in voice
- `/leave` - Disconnect
- Pytgcalls integration for group voice

---

### 4. **Service Layer** (`app/services/`)

Business logic and external integrations.

#### 4.1 **Database Service** (`database.py`)

**Models:**
```python
class User:
    user_id: int            # Telegram user ID
    username: str           # @username
    language: str           # User language
    audio_bitrate: str      # Preferred audio quality
    video_resolution: str   # Preferred video quality
    created_at: DateTime    # Registration date
    last_active: DateTime   # Last activity

class Favorite:
    user_id: int
    track_id: str
    title: str
    source: str             # youtube, soundcloud, etc
    url: str
    duration: int           # seconds
    added_at: DateTime

class History:
    user_id: int
    track_id: str
    title: str
    source: str
    action: str             # 'downloaded' or 'listened'
    accessed_at: DateTime

class Queue:
    user_id: int
    track_id: str
    title: str
    position: int           # Order in queue
    added_at: DateTime

class FileCache:
    track_id: str           # Unique per track
    file_path: str          # Local file path
    file_size_mb: float
    format: str             # 'mp3' or 'mp4'
    quality: str            # '192kbps' or '720p'
    created_at: DateTime
    last_accessed: DateTime
```

**Database Connection:**
```
┌──────────────────────┐
│ SQLAlchemy (ORM)     │
│ - Query building     │
│ - Model mapping      │
└──────────┬───────────┘
           │
┌──────────▼───────────────┐
│ AsyncSession             │
│ - Async query execution  │
│ - Connection pooling     │
└──────────┬───────────────┘
           │
┌──────────▼───────────────┐
│ asyncpg driver           │
│ - PostgreSQL adapter     │
│ - Binary protocol        │
└──────────┬───────────────┘
           │
┌──────────▼───────────────┐
│ PostgreSQL 15+           │
│ - Data persistence       │
│ - ACID transactions      │
└──────────────────────────┘
```

**Pool Configuration:**
- Pool size: 20 connections
- Max overflow: 10 extra connections
- Pool pre_ping: Health check before use

#### 4.2 **Redis Service** (`redis_service.py`)

**Purpose:**
- Search result caching
- Rate limit tracking
- Temporary data storage
- Session management

**Operations:**
```python
# Key operations
await redis.set(key, value, ttl=600)     # 10 min default
await redis.get(key)                     # Retrieve with auto-JSON decode
await redis.delete(key)                  # Remove key
await redis.increment(key, amount=1)     # Counter operations
await redis.exists(key)                  # Check presence
await redis.get_ttl(key)                 # Remaining TTL
```

**Cache Keys:**
```
search:{query}                # Search results
rate_limit:{user_id}:{minute} # Rate limit tracking
user_session:{user_id}        # Session data
favorite:{user_id}            # Favorite shortcuts
```

#### 4.3 **Media Downloader** (`downloader.py`)

**Search Platforms:**
- YouTube (primary)
- SoundCloud
- Vimeo
- Instagram
- TikTok
- Spotify

**Download Architecture:**
```python
class MediaDownloader:
    async def search(query, source="youtube", limit=5)
        # Uses yt-dlp for unified interface
        ├── YouTube: video search
        ├── SoundCloud: track search
        ├── Generic: playlist extraction
        └── Returns: List[{id, title, duration, uploader, url, thumbnail, source}]
    
    async def download_audio(url, bitrate="192", progress_callback=None)
        # MP3 download and encoding
        ├── Use semaphore (max 3 concurrent)
        ├── Download with yt-dlp
        ├── Encode with FFmpeg
        └── Cache result
    
    async def download_video(url, resolution="720", progress_callback=None)
        # MP4 download and encoding
        ├── Use semaphore (max 3 concurrent)
        ├── Download best audio+video
        ├── Merge with FFmpeg
        └── Cache result
    
    async def get_playlist_tracks(url)
        # Extract all tracks from playlist
        └── Returns: List of track URLs
```

**Quality Settings:**
```
Audio Bitrates:
- 96 kbps   (Low quality, small size)
- 128 kbps  (Standard quality)
- 192 kbps  (High quality, default)
- 320 kbps  (Maximum quality, large size)

Video Resolutions:
- 480p (small)
- 720p (standard, default)
- 1080p (high)
```

**Concurrency Control:**
```python
_download_semaphore = asyncio.Semaphore(3)  # Max 3 concurrent

async def download_audio(self, url, bitrate, progress_callback):
    async with self._download_semaphore:
        # Only 3 downloads in parallel
```

#### 4.4 **Cloud Storage Services**

**Google Drive Service** (`cloud_storage/google_drive.py`)
```python
class GoogleDriveService:
    async def upload_file(file_path, folder_id)
        # Upload file to Google Drive
        # Returns: shareable URL
    
    async def delete_file(file_id)
        # Remove file from Drive
    
    async def get_quota()
        # Check storage quota
```

**Dropbox Service** (`cloud_storage/dropbox.py`)
```python
class DropboxService:
    async def upload_file(file_path, remote_path)
        # Upload to Dropbox
        # Returns: shareable link
    
    async def delete_file(remote_path)
        # Remove from Dropbox
```

**When Used:**
- File size > MAX_FILE_SIZE_MB (50MB default)
- Local cache full
- Fallback for redundancy

---

### 5. **Utility Layer** (`app/utils/`)

#### 5.1 **Logger** (`logger.py`)
```python
# Rotating file handler (10MB per file, 5 backups)
# Console handler for real-time monitoring
# Log format: "timestamp - logger - level - message"

logger.info("User search")      # Regular info
logger.error("Connection failed") # Errors
logger.warning("Low disk space")  # Warnings
```

#### 5.2 **Rate Limiter** (`rate_limiter.py`)
```python
class RateLimiter:
    is_allowed(user_id)         # Check if request allowed
    get_retry_after(user_id)    # Seconds until next allowed

# Per-user tracking: 5 requests/minute
# In-memory for single instance, Redis-backed for distributed
```

#### 5.3 **Helpers** (`helpers.py`)
```python
format_duration(seconds)         # "1:23:45" formatting
extract_urls(text)              # Find URLs in text
get_source_from_url(url)        # Detect: youtube, soundcloud, etc
get_file_size_mb(path)          # Calculate file size
get_cache_size_gb()             # Total cache directory size
clean_cache(max_age_days, max_size_gb)  # Delete old/excess files
escape_markdown(text)           # Telegram MarkdownV2 escaping
truncate_text(text, max_length) # Add ellipsis if too long
```

---

## Data Flow

### Search Flow
```
User: /search "song name"
    ↓
commands.py: search_handler()
    ├── Rate limit check
    ├── Log search
    └── Display search menu
    
User clicks search button
    ↓
search.py: search_command()
    ├── Query: "song name"
    ├── Check Redis cache
    │   ├── Hit: Return cached results
    │   └── Miss: Call MediaDownloader.search()
    ├── Cache results in Redis (10 min TTL)
    └── Display first page (5 results)
    
Results displayed with buttons
    ├── 🎧 Listen (download immediately)
    ├── 📱 MP3 (select bitrate)
    ├── 🎬 MP4 (select resolution)
    └── ❤️ Add to favorites
```

### Download Flow
```
User: Clicks "MP3" button
    ↓
search.py: track_action_handler()
    ├── Show bitrate selection: [96, 128, 192, 320]
    └── Wait for selection
    
User: Selects "192 kbps"
    ↓
download.py: download_audio_handler()
    ├── Check cache (track_id + bitrate)
    │   ├── Hit: Send cached file
    │   └── Miss: Download
    ├── Check rate limit
    ├── Acquire semaphore (max 3)
    ├── Download with yt-dlp
    ├── Encode with FFmpeg to 192 kbps MP3
    ├── Cache file locally
    │   └── FileCache model: track_id, file_path, size, quality
    ├── Upload to cloud if > 50MB
    ├── Send to user
    └── Add to history
```

### Queue Flow
```
User: /add <number>
    ↓
commands.py: add_handler()
    ├── Validate number from search results
    ├── Add to database Queue table
    ├── Set position = current_max + 1
    └── Confirm to user
    
User: /queue
    ↓
commands.py: queue_handler()
    ├── Query Database
    │   └── SELECT * FROM queue WHERE user_id = ? ORDER BY position
    ├── Display tracks with ➡️ buttons
    └── Button: /play or /skip
```

---

## Database Schema

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    language VARCHAR(10) DEFAULT 'en',
    audio_bitrate VARCHAR(10) DEFAULT '192',
    video_resolution VARCHAR(10) DEFAULT '720',
    created_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_user_id ON users(user_id);

-- Favorites table
CREATE TABLE favorites (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    track_id VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    source VARCHAR(50),
    url TEXT,
    duration INT,
    added_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
CREATE INDEX idx_favorites_user ON favorites(user_id);

-- History table
CREATE TABLE history (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    track_id VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    source VARCHAR(50),
    url TEXT,
    duration INT,
    action VARCHAR(50),  -- 'downloaded' or 'listened'
    accessed_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
CREATE INDEX idx_history_user ON history(user_id);

-- Queue table
CREATE TABLE queue (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    track_id VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    source VARCHAR(50),
    url TEXT,
    duration INT,
    position INT,
    added_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
CREATE INDEX idx_queue_user ON queue(user_id);

-- File Cache table
CREATE TABLE file_cache (
    id SERIAL PRIMARY KEY,
    track_id VARCHAR(255) UNIQUE NOT NULL,
    file_path TEXT NOT NULL,
    file_size_mb FLOAT,
    format VARCHAR(10),  -- 'mp3' or 'mp4'
    quality VARCHAR(20), -- '192kbps' or '720p'
    created_at TIMESTAMP DEFAULT NOW(),
    last_accessed TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_cache_track ON file_cache(track_id);
```

---

## Concurrency Model

### Request Handling
```
Telegram User sends message/callback
    ↓
python-telegram-bot receives via polling/webhook
    ↓
Adds to async queue
    ↓
Asyncio event loop processes
    ├── Database: AsyncSession (pool of 20)
    ├── Redis: RedisService (async connection)
    ├── Download: Semaphore (max 3 concurrent)
    └── APIs: aiohttp for external calls
    
Max concurrent requests: Limited by database pool (20)
```

### Search Operations
```
Multiple users searching simultaneously
    ↓
Each calls MediaDownloader.search()
    ├── Uses yt-dlp (non-blocking)
    └── Results cached in Redis
    
Results stored per query in Redis
    └── If same query: Return cached (10 min)
    └── If different query: Download fresh
```

### Download Operations
```
Multiple download requests
    ↓
Each acquires semaphore
    ├── Max 3 concurrent downloads
    ├── Uses FFmpeg (CPU intensive)
    └── Others wait in queue
    
System protected from overload
    └── CPU stays reasonable
    └── Bandwidth stays manageable
```

---

## Deployment Architecture

### Docker Deployment
```
Host System
└── Docker Daemon
    ├── Container: PostgreSQL (Port 5432)
    │   └── Volume: postgres_data
    ├── Container: Redis (Port 6379)
    │   └── Volume: redis_data
    └── Container: Bot (Internal network)
        ├── Volume: /app/cache (downloads)
        ├── Volume: /app/logs (logging)
        └── Connects to postgres and redis via service names
```

### Communication
```
Bot ──HTTP──> Telegram API
    ├── Polling (check for updates)
    └── Sending responses

Bot ──TCP──> PostgreSQL
    ├── User queries
    ├── Favorites/History
    └── Queue management

Bot ──TCP──> Redis
    ├── Search cache
    ├── Rate limiting
    └── Session data

Bot ──HTTP──> External APIs
    ├── YouTube/SoundCloud (via yt-dlp)
    ├── Google Drive (cloud storage)
    ├── Dropbox (cloud storage)
    └── Spotify (music metadata)
```

---

## Performance Considerations

### Database Performance
- Connection pooling: Max 20 concurrent queries
- Indexes on frequently queried columns
- Query optimization through SQLAlchemy
- Regular VACUUM and ANALYZE

### Cache Performance
- Redis for fast search results (10 min TTL)
- Local filesystem for MP3/MP4 files (7 days TTL)
- Max 10GB cache with auto-cleanup

### Download Performance
- Semaphore limits concurrent downloads (3 max)
- FFmpeg multi-threading for encoding
- Bitrate selection reduces file size
- Progress callbacks for user feedback

### API Performance
- Rate limiting: 5 requests/minute per user
- Search caching prevents duplicate queries
- Async operations prevent blocking
- Connection pooling for database

---

## Scalability Plan

### Single Instance (Current)
- 1 bot container
- 1 PostgreSQL instance
- 1 Redis instance
- Cache on local disk

### Multiple Instances (Future)
- N bot containers
- 1 PostgreSQL instance (shared)
- 1 Redis instance (shared)
- Distributed cache on shared storage
- Load balancer

### Distributed System (Enterprise)
- Multiple bots across servers
- PostgreSQL replication
- Redis cluster
- S3/Google Cloud Storage for caches
- Message queue (RabbitMQ) for task distribution

---

**Architecture designed for:** Reliability, Scalability, and Maintainability
