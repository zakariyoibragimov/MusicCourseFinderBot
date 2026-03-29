# 🚀 Quick Start Guide - Telegram Music Bot

Complete step-by-step guide to get the music bot running.

## Prerequisites

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **PostgreSQL 15+** - [Download](https://www.postgresql.org/download/)
- **Redis 7+** - [Download](https://redis.io/download/)
- **FFmpeg** - [Download](https://ffmpeg.org/download.html)
- **Docker + Docker Compose** (optional) - [Download](https://www.docker.com/products/docker-desktop)
- **Telegram Bot Token** - [@BotFather](https://t.me/BotFather)

---

## 🐳 Option A: Quick Start with Docker (Recommended)

### 1. Prepare Environment

```bash
# Copy template
cp .env.example .env

# Edit .env
# Open .env and set:
#   BOT_TOKEN = your_bot_token_from_botfather
#   ADMIN_ID = your_telegram_user_id
# (Optional) Google Drive, Dropbox, Spotify credentials
```

### 2. Start Services

```bash
# Build and start all services
docker-compose up -d

# Check services are running
docker-compose ps

# Expected output:
# postgres   3/3 healthy
# redis      1/1 healthy  
# bot        running
```

### 3. Test the Bot

```bash
# Send /start command in Telegram
# Bot should respond with main menu
```

### 4. View Logs

```bash
# See bot logs
docker-compose logs -f bot

# See all logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## 💻 Option B: Local Installation (Linux/macOS)

### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv postgresql redis-server ffmpeg
```

**macOS:**
```bash
brew install python@3.11 postgresql redis ffmpeg
brew services start postgresql
brew services start redis
```

### 2. Create Virtual Environment

```bash
# Create environment
python3.11 -m venv venv

# Activate environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
```

### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Setup Database

```bash
# Start PostgreSQL
# Ubuntu: sudo systemctl start postgresql
# macOS: brew services start postgresql

# Create database
createdb music_bot_db

# Create database user
sudo -u postgres psql -c "CREATE USER music_bot WITH PASSWORD 'your_secure_password';"
sudo -u postgres psql -c "ALTER ROLE music_bot WITH CREATEDB;"
```

### 5. Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit .env with your values:
nano .env
```

Required settings:
```env
BOT_TOKEN=your_bot_token
ADMIN_ID=your_telegram_id
DB_USER=music_bot
DB_PASSWORD=your_secure_password
DB_NAME=music_bot_db
DB_HOST=localhost
DB_PORT=5432
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 6. Initialize Database

```bash
# Create all tables
python init_db.py

# Expected output:
# ✅ Database connection established
# ✅ Database tables created successfully!
```

### 7. Start the Bot

```bash
# Activate venv if not already active
source venv/bin/activate

# Run bot
python -m app.main

# Expected output:
# 2024-01-XX XX:XX:XX INFO Starting polling
# Bot is running... Press Ctrl+C to stop
```

---

## 🪟 Option C: Windows Local Installation

### 1. Install Dependencies

- **Python 3.11+** from [python.org](https://www.python.org/downloads/)
- **PostgreSQL** from [postgresql.org](https://www.postgresql.org/download/windows/)
- **Redis** - Use Windows Subsystem for Linux (WSL2) or [native Windows build](https://github.com/microsoftarchive/redis/releases)
- **FFmpeg** - Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH

### 2. Setup Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate
```

### 3. Install Python Packages

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Setup PostgreSQL

Using pgAdmin (installed with PostgreSQL):

1. Open pgAdmin
2. Create new database: `music_bot_db`
3. Create new role: `music_bot` with password
4. Grant privileges to the role

Or using command line:

```bash
# Open PostgreSQL command prompt
createdb -U postgres music_bot_db
createuser -U postgres -P music_bot
```

### 5. Configure Environment

```bash
# Copy template
copy .env.example .env

# Edit .env in your editor (Notepad, VS Code, etc.)
# Set your BOT_TOKEN, ADMIN_ID, and database credentials
```

### 6. Initialize Database

```bash
python init_db.py
```

### 7. Start the Bot

```bash
python -m app.main
```

---

## 🔑 Getting Your Credentials

### Telegram Bot Token

1. Open [@BotFather](https://t.me/BotFather) in Telegram
2. Send `/newbot` command
3. Choose a name for your bot
4. Choose a username (must end with "bot")
5. BotFather will give you the token, copy it to `BOT_TOKEN` in `.env`

### Your Telegram User ID

1. Open [@userinfobot](https://t.me/userinfobot) in Telegram
2. Bot will show your User ID
3. Copy it to `ADMIN_ID` in `.env`

### PostgreSQL Connection

For local installation:
- **Host**: localhost (or 127.0.0.1)
- **Port**: 5432 (default)
- **User**: postgres (or newly created user)
- **Password**: your chosen password
- **Database**: music_bot_db

### Redis Connection

For local installation:
- **Host**: localhost (or 127.0.0.1)
- **Port**: 6379 (default)
- **Password**: empty (unless configured)

---

## 🎵 Bot Commands

After starting, these commands are available:

| Command | Description |
|---------|-------------|
| `/start` | Show main menu |
| `/help` | Show help and tips |
| `/search <query>` | Search for music |
| `/settings` | Configure quality and language |
| `/queue` | Show current queue |
| `/history` | Show recent downloads |
| `/favorites` | Show saved tracks |
| `/popular` | Show trending tracks |
| `/play` | Start playback |
| `/skip` | Skip to next track |
| `/add <number>` | Add track to queue |
| `/clear_cache` | Clear download cache (admin) |

---

## 🐛 Troubleshooting

### Bot not responding

1. Check bot token in `.env` is correct
2. Check PostgreSQL is running: `psql -U postgres -d music_bot_db`
3. Check Redis is running: `redis-cli ping` (should return "PONG")
4. Check logs: `docker-compose logs bot` or terminal output

### Database connection error

```bash
# For Docker:
docker-compose ps  # Check if postgres is healthy

# For local:
psql -h localhost -U music_bot -d music_bot_db -W  # Try connecting
```

### FFmpeg not found

```bash
# Ubuntu/Debian:
sudo apt-get install ffmpeg

# macOS:
brew install ffmpeg

# Windows:
# Download from https://ffmpeg.org/download.html
# Add to system PATH
ffmpeg -version  # Verify installation
```

### Port already in use

```bash
# Find process using port
lsof -i :5432      # PostgreSQL
lsof -i :6379      # Redis
lsof -i :8000      # Bot (if configured)

# Kill process
kill -9 <PID>
```

### Out of disk space (cache issues)

```bash
# Clear cache manually
python -c "from app.utils.helpers import clean_cache; clean_cache(max_age_days=7, max_size_gb=10)"

# Or use bot command
/clear_cache
```

---

## 📝 Configuration Options

All options in `.env.example`:

- **Bot settings**: Token, admin ID
- **Database**: PostgreSQL connection
- **Cache**: Redis connection
- **Media quality**: Audio bitrate, video resolution
- **Cloud storage**: Google Drive, Dropbox credentials
- **APIs**: Spotify authentication
- **Rate limiting**: Requests per minute
- **File limits**: Max file sizes

See `README.md` for full documentation.

---

## 🚀 Deployment

### Production Deployment with Docker

```bash
# Build image
docker build -t music-bot:latest .

# Run with custom environment
docker run -d \
  -e BOT_TOKEN=your_token \
  -e ADMIN_ID=your_id \
  -e DB_HOST=postgres_host \
  -v /path/to/cache:/app/cache \
  -v /path/to/logs:/app/logs \
  music-bot:latest
```

### Using docker-compose in Production

```bash
# Edit docker-compose.yml for production
nano docker-compose.yml

# Set secure passwords for PostgreSQL and Redis
# Configure volumes for persistence
# Add resource limits

# Deploy
docker-compose -f docker-compose.yml up -d
```

---

## 📞 Support

For issues or questions:

1. Check logs: `docker-compose logs bot`
2. Review README.md for full documentation
3. Check .env configuration
4. Verify all services are running
5. Check internet connection for downloads

---

## 📄 License

MIT - See LICENSE file for details

---

## ✨ Features

✅ Multi-source search (YouTube, SoundCloud, etc.)
✅ MP3 and MP4 downloads with quality selection
✅ Playlist support
✅ Favorites and history
✅ Queue management
✅ Voice chat support (groups)
✅ Inline search in any chat
✅ Rate limiting and caching
✅ Cloud storage fallback
✅ Production-ready with Docker

---

**Happy listening! 🎵**
