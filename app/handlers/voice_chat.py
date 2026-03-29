"""
Voice chat handlers for group voice channel playback using pytgcalls
"""

from telegram import Update
from telegram.ext import ContextTypes
from app.utils.logger import logger
from app.locales import get_text


async def join_voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /join command - join voice chat"""
    lang = context.user_data.get("lang", "ru")
    await update.message.reply_text(get_text("voice_chat_unavailable", lang))
    logger.info(f"Join voice: {update.effective_user.id}")


async def play_voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /play in voice - play track in group voice channel"""
    lang = context.user_data.get("lang", "ru")
    await update.message.reply_text(get_text("voice_play_unavailable", lang))
    logger.info(f"Play voice: {update.effective_user.id}")


async def pause_voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /pause - pause voice playback"""
    lang = context.user_data.get("lang", "ru")
    await update.message.reply_text(get_text("voice_pause_unavailable", lang))
    logger.info(f"Pause voice: {update.effective_user.id}")


async def resume_voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /resume - resume voice playback"""
    lang = context.user_data.get("lang", "ru")
    await update.message.reply_text(get_text("voice_resume_unavailable", lang))
    logger.info(f"Resume voice: {update.effective_user.id}")


async def leave_voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /leave - disconnect from voice chat"""
    lang = context.user_data.get("lang", "ru")
    await update.message.reply_text(get_text("voice_leave_unavailable", lang))
    logger.info(f"Leave voice: {update.effective_user.id}")


async def now_playing_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /nowplaying - show current track in voice"""
    lang = context.user_data.get("lang", "ru")
    await update.message.reply_text(get_text("voice_now_playing_unavailable", lang))
    logger.info(f"Now playing: {update.effective_user.id}")
