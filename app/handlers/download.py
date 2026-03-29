"""
Download handlers for MP3 and MP4
"""

from telegram import Update
from telegram.ext import ContextTypes
from app.utils.logger import logger
from app.services.downloader import MediaDownloader
from app.locales import get_text
from app.utils.media_delivery import send_downloaded_audio, send_downloaded_video
from app.utils.subscription import ensure_music_access


async def download_quality_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle quality selection before download"""
    
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "ru")
    
    await query.message.reply_text(
        get_text("quality_selection_hint", lang)
    )
    logger.info(f"Download quality selected: {query.data}")


async def download_audio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle MP3 download"""
    
    query = update.callback_query
    await query.answer()
    if not await ensure_music_access(update, context):
        return
    lang = context.user_data.get("lang", "ru")
    
    parts = query.data.split("_", 3)
    if len(parts) < 4:
        await query.message.reply_text(get_text("invalid_callback_data", lang))
        return

    _, _, bitrate, track_id = parts
    status_msg = await query.message.reply_text(get_text("downloading", lang), parse_mode="HTML")
    dl = context.bot_data.get("downloader") or MediaDownloader()
    result = await dl.download_audio(
        f"https://youtube.com/watch?v={track_id}",
        bitrate=bitrate,
    )
    await send_downloaded_audio(query.message, result, lang, status_message=status_msg)
    logger.info(f"MP3 download initiated: {query.data}")


async def download_video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle MP4 download"""
    
    query = update.callback_query
    await query.answer()
    if not await ensure_music_access(update, context):
        return
    lang = context.user_data.get("lang", "ru")
    
    parts = query.data.split("_", 3)
    if len(parts) < 4:
        await query.message.reply_text(get_text("invalid_callback_data", lang))
        return

    _, _, resolution, track_id = parts
    status_msg = await query.message.reply_text(get_text("downloading", lang), parse_mode="HTML")
    dl = context.bot_data.get("downloader") or MediaDownloader()
    result_path = await dl.download_video(
        f"https://youtube.com/watch?v={track_id}",
        resolution=resolution,
    )
    await send_downloaded_video(query.message, result_path, lang, status_message=status_msg)
    logger.info(f"MP4 download initiated: {query.data}")
