"""
Playback handlers for listening to tracks
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.utils.logger import logger


async def play_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /play command - play from queue"""
    
    # TODO: Get first track from user's queue
    # Download if not in cache
    # Send audio file to user
    
    logger.info(f"Play command: {update.effective_user.id}")


async def skip_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /skip command - skip to next track"""
    
    # TODO: Move to next track in queue
    # If queue empty, notify user
    
    logger.info(f"Skip command: {update.effective_user.id}")


async def queue_add_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle adding track to queue from search results"""
    
    # TODO: Add track to user's queue
    # Show queue position
    
    logger.info(f"Track added to queue: {update.effective_user.id}")


async def listen_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle 'Listen' button - play track immediately"""
    
    query = update.callback_query
    await query.answer()
    
    # Parse callback: listen_track_id
    
    # TODO: Download track and send audio file
    # Add to history
    
    logger.info(f"Listen handler: {query.data}")
