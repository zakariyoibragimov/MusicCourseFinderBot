"""
Database initialization script

Run this script to create all database tables:
    python init_db.py

Or use Alembic for migrations:
    alembic upgrade head
"""

import asyncio
import sys
import os
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import Config
from app.services.database import DatabaseService
from app.utils.logger import logger, setup_logging


async def main():
    """Initialize database tables"""
    
    # Setup logging
    setup_logging()
    
    logger.info("=" * 60)
    logger.info("DATABASE INITIALIZATION SCRIPT")
    logger.info("=" * 60)
    
    try:
        logger.info(f"📋 Configuration loaded from environment")
        logger.info(f"   Database: {Config.DB_NAME} @ {Config.DB_HOST}:{Config.DB_PORT}")
        logger.info(f"   Redis: {Config.REDIS_HOST}:{Config.REDIS_PORT}")
        
        # Validate config
        Config.validate(require_bot=False)
        logger.info("✅ Configuration validated")
        
        # Initialize database service
        db_service = DatabaseService(Config.DATABASE_URL)
        logger.info("🔗 Connecting to database...")
        
        await db_service.initialize()
        logger.info("✅ Database connection established")
        
        # All tables should be created automatically via SQLAlchemy
        logger.info("✅ Database tables created successfully!")
        logger.info("")
        logger.info("Created tables:")
        logger.info("  • users - User profiles and preferences")
        logger.info("  • favorites - User favorite tracks")
        logger.info("  • history - Download/listen history")
        logger.info("  • queue - User's playback queue")
        logger.info("  • file_cache - Downloaded files metadata")
        logger.info("")
        
        # Close connection
        await db_service.close()
        logger.info("✅ Database disconnected")
        logger.info("")
        logger.info("=" * 60)
        logger.info("✨ Database initialization completed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        logger.error("Please check:")
        logger.error("  1. PostgreSQL is running")
        logger.error("  2. Connection credentials in .env file are correct")
        logger.error("  3. Database exists and is accessible")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
