# 🚀 Production Deployment Guide

Complete guide for deploying the Telegram music bot to production.

## Table of Contents

1. [Server Setup](#server-setup)
2. [Docker Deployment](#docker-deployment)
3. [SSL/HTTPS Configuration](#sslauthentication)
4. [Database Backups](#database-backups)
5. [Monitoring & Logging](#monitoring--logging)
6. [Performance Optimization](#performance-optimization)
7. [Security Hardening](#security-hardening)
8. [Troubleshooting](#troubleshooting)

---

## Server Setup

### Recommended Server Specs

- **CPU**: 2+ cores (4 recommended for scalability)
- **RAM**: 4GB minimum (8GB for high-traffic)
- **Storage**: 50GB+ SSD (100GB+ if caching many files)
- **Network**: Stable 100Mbps+ connection
- **OS**: Ubuntu 22.04 LTS or CentOS 8+

### Initial Server Configuration

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install security tools
sudo apt-get install -y ufw fail2ban curl wget git nano

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add current user to docker group
sudo usermod -aG docker $USER

# Verify Docker installation
docker --version
docker-compose --version
```

---

## Docker Deployment

### 1. Prepare Production .env

```bash
# Create production environment file
sudo nano /opt/music-bot/.env

# Critical settings for production:
BOT_TOKEN=your_bot_token_here
ADMIN_ID=your_admin_id
DB_USER=secure_username
DB_PASSWORD=generate_secure_password  # Use: python -c "import secrets; print(secrets.token_urlsafe(32))"
DB_NAME=music_bot_db
DB_HOST=postgres
DB_PORT=5432
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=generate_secure_password

# Quality settings (can adjust)
DEFAULT_AUDIO_BITRATE=192
DEFAULT_VIDEO_RESOLUTION=720
MAX_CONCURRENT_DOWNLOADS=3

# File limits
MAX_FILE_SIZE_MB=50
PREMIUM_FILE_SIZE_MB=2000

# Cache configuration
CACHE_TTL=600
CACHE_FILE_TTL=604800
CACHE_MAX_SIZE_GB=50

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/bot.log

# Timezone
TZ=UTC
```

### 2. Production docker-compose.yml

Update docker-compose.yml for production:

```yaml
# Key changes:
services:
  postgres:
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups  # For database backups
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    restart: always
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  bot:
    restart: always
    build: .
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./cache:/app/cache
      - ./logs:/app/logs
    environment:
      # All from .env file
      - BOT_TOKEN=${BOT_TOKEN}
      - ADMIN_ID=${ADMIN_ID}
      # ... other variables

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
```

### 3. Deploy Application

```bash
# Create application directory
sudo mkdir -p /opt/music-bot
cd /opt/music-bot

# Copy project files
sudo git clone <your-repo-url> .
# or
sudo cp -r /path/to/project/* .

# Set proper permissions
sudo chown -R $USER:$USER /opt/music-bot

# Start services
docker-compose up -d

# Verify all services
docker-compose ps

# Check bot logs
docker-compose logs -f bot

# Create database tables
docker-compose exec bot python init_db.py
```

### 4. Health Checks & Monitoring

```bash
# Check service status
docker-compose ps

# View service logs
docker-compose logs -f bot
docker-compose logs -f postgres
docker-compose logs -f redis

# Monitor resource usage
docker stats

# Restart specific service
docker-compose restart bot

# Full restart
docker-compose restart
```

---

## SSL/HTTPS Configuration

### Using Let's Encrypt with Nginx Reverse Proxy

```bash
# Install Nginx
sudo apt-get install -y nginx certbot python3-certbot-nginx

# Create Nginx config
sudo nano /etc/nginx/sites-available/music-bot

# Add configuration:
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Create symlink
sudo ln -s /etc/nginx/sites-available/music-bot /etc/nginx/sites-enabled/

# Test nginx config
sudo nginx -t

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

## Database Backups

### Manual Backup

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U ${DB_USER} ${DB_NAME} > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup Redis
docker-compose exec redis redis-cli BGSAVE

# Backup cache
tar -czf cache_backup_$(date +%Y%m%d_%H%M%S).tar.gz cache/
```

### Automated Daily Backups

```bash
# Create backup script
sudo nano /opt/music-bot/backup.sh

#!/bin/bash
BACKUP_DIR="/opt/music-bot/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# PostgreSQL backup
docker-compose exec -T postgres pg_dump -U music_bot music_bot_db | gzip > $BACKUP_DIR/postgres_$TIMESTAMP.sql.gz

# Redis backup
docker-compose exec -T redis redis-cli BGSAVE >/dev/null

# Compress logs for archive
tar -czf $BACKUP_DIR/logs_$TIMESTAMP.tar.gz logs/

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $TIMESTAMP"

# Add to crontab
sudo crontab -e

# Add line:
# 0 2 * * * /opt/music-bot/backup.sh >> /opt/music-bot/logs/backup.log 2>&1
```

### Restore from Backup

```bash
# Stop bot
docker-compose stop bot

# Restore PostgreSQL
docker-compose exec postgres psql -U music_bot music_bot_db < backup_20240101_120000.sql

# Restart bot
docker-compose start bot
```

---

## Monitoring & Logging

### Log Aggregation

```bash
# View bot logs
docker-compose logs -f bot --tail=100

# Search logs for errors
docker logs <container-id> | grep ERROR

# Save logs to file
docker-compose logs bot > bot_logs_$(date +%Y%m%d).txt
```

### Monitoring Tools

Install Prometheus + Grafana for monitoring:

```bash
# Create docker-compose addition for monitoring
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    environment:
      GF_SECURITY_ADMIN_PASSWORD=admin
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  prometheus_data:
  grafana_data:
```

### Bot Alerts

Create monitoring script:

```python
# monitoring.py
import asyncio
from app.services.database import DatabaseService
from app.services.redis_service import RedisService
import logging

async def check_system_health():
    """Check bot system health"""
    try:
        # Check database
        async with db_session() as session:
            await session.execute("SELECT 1")
        
        # Check Redis
        await redis_service.get("health_check")
        
        # Check disk space
        import shutil
        disk = shutil.disk_usage("/")
        if disk.free < 10_000_000_000:  # Less than 10GB
            logging.warning(f"Low disk space: {disk.free / 1e9:.2f}GB")
        
        logging.info("✅ System health check: OK")
        return True
    except Exception as e:
        logging.error(f"❌ System health check failed: {e}")
        return False

# Run every hour
asyncio.create_task(check_system_health())
```

---

## Performance Optimization

### Database Optimization

```sql
-- Create indexes for faster queries
CREATE INDEX idx_user_id ON users(user_id);
CREATE INDEX idx_history_user ON history(user_id);
CREATE INDEX idx_favorites_user ON favorites(user_id);
CREATE INDEX idx_queue_user ON queue(user_id);
CREATE INDEX idx_cache_track ON file_cache(track_id);

-- Analyze tables
ANALYZE users;
ANALYZE history;
ANALYZE favorites;
ANALYZE queue;
ANALYZE file_cache;
```

### Cache Optimization

```python
# Adjust cache settings in .env
CACHE_TTL=600              # 10 minutes for search cache
CACHE_FILE_TTL=604800      # 7 days for file cache
CACHE_MAX_SIZE_GB=100      # 100GB max cache

# Redis persistence settings
redis_service.execute("CONFIG SET save '300 10 60 10000'")
```

### Connection Pooling

```python
# In database.py - already optimized with connection pooling:
create_async_engine(
    db_url,
    pool_size=20,              # Max pool size
    max_overflow=10,           # Extra connections allowed
    pool_pre_ping=True,        # Check connection health
    echo=False,
)
```

---

## Security Hardening

### Application Security

```bash
# 1. Update packages regularly
docker-compose pull
docker-compose down
docker-compose up -d

# 2. Use environment variables for secrets
# Never hardcode credentials in Dockerfile

# 3. Regular security audits
docker scan music-bot:latest

# 4. Keep dependencies updated
pip install --upgrade -r requirements.txt
```

### Database Security

```bash
# 1. Strong passwords
DB_PASSWORD=$(openssl rand -base64 32)

# 2. Limit database access
# Only allow connection from bot service

# 3. Regular backups
# Automated daily backups (see backup section)

# 4. Enable SSL for PostgreSQL
PGSSL=require
```

### Network Security

```bash
# 1. Firewall configuration (ufw)
sudo ufw status
sudo ufw allow 22/tcp
sudo ufw allow 443/tcp
sudo ufw deny 5432/tcp  # Block direct database access

# 2. Rate limiting (already in bot)
# /app/utils/rate_limiter.py - 5 requests/minute per user

# 3. SSH key authentication
ssh-keygen -t ed25519 -f ~/.ssh/id_music_bot
# Add to server authorized_keys
```

### Bot Security

```python
# In handlers/commands.py - admin-only decorator
@admin_only
async def clear_cache_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Only ADMIN_ID can use this"""
    pass

# File size limits (configured in .env)
MAX_FILE_SIZE_MB=50
PREMIUM_FILE_SIZE_MB=2000

# Rate limiting per user
REQUESTS_PER_MINUTE=5
```

---

## Troubleshooting

### Bot Not Responding

```bash
# 1. Check if container is running
docker-compose ps

# 2. Check logs
docker-compose logs bot

# 3. Verify network connectivity
docker-compose exec bot curl -I https://www.youtube.com

# 4. Check database connection
docker-compose exec bot python -c "from app.config import Config; from app.services.database import DatabaseService; import asyncio; asyncio.run(DatabaseService(Config()).initialize())"
```

### High Memory Usage

```bash
# 1. Check memory consumption
docker stats

# 2. Reduce cache size
# Edit .env: CACHE_MAX_SIZE_GB=50

# 3. Clear old cache files
docker-compose exec bot python -c "from app.utils.helpers import clean_cache; clean_cache(max_age_days=7)"

# 4. Restart services
docker-compose restart
```

### Database Performance Issues

```bash
# 1. Check database size
docker-compose exec postgres psql -U music_bot -c "SELECT pg_size_pretty(pg_database_size('music_bot_db'));"

# 2. Analyze queries
docker-compose exec postgres psql -U music_bot -c "EXPLAIN ANALYZE SELECT * FROM history;"

# 3. Vacuum database
docker-compose exec postgres psql -U music_bot -c "VACUUM ANALYZE;"
```

### Disk Space Issues

```bash
# 1. Check disk usage
df -h

# 2. Find large files
du -sh /opt/music-bot/*

# 3. Clean cache
docker-compose exec bot python -c "from app.utils.helpers import clean_cache; clean_cache(max_age_days=3, max_size_gb=30)"

# 4. Compress old logs
find /opt/music-bot/logs -name "*.log" -mtime +30 | xargs gzip
```

---

## Scaling Considerations

### Horizontal Scaling (Multiple Bots)

For handling multiple bot instances:

1. Use single PostgreSQL + Redis (shared)
2. Run multiple bot containers on different servers
3. Use load balancing for API requests
4. Implement distributed rate limiting with Redis

### Vertical Scaling (Increasing Resources)

```bash
# Increase resource limits
docker-compose.yml:
services:
  bot:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

---

## Maintenance Checklist

- [ ] Daily backups verified
- [ ] Logs monitored for errors
- [ ] Database health checked
- [ ] Disk space monitored
- [ ] Dependencies updated monthly
- [ ] Security patches applied
- [ ] Rate limiting working correctly
- [ ] Cache cleanup running

---

**Successfully deployed! 🎉**
