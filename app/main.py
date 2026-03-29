"""
Main application file for Telegram music bot
Initializes all handlers, services, and runs the bot
"""

import asyncio
from difflib import SequenceMatcher
from telegram.error import TimedOut, NetworkError
from telegram.request import HTTPXRequest
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    InlineQueryHandler, CallbackQueryHandler
)

from app.config import Config
from app.utils.logger import setup_logging, logger
from app.utils.media_delivery import send_downloaded_audio
from app.services.database import DatabaseService
from app.services.downloader import MediaDownloader
from app.services.redis_service import RedisService
from app.handlers.commands import (
    start_handler, help_handler, search_handler, settings_handler,
    queue_handler, history_handler, favorites_handler, popular_handler,
    clear_cache_handler, admin_only,
    play_handler, skip_handler, queue_add_handler,
    menu_callback_handler, language_set_handler, settings_callback_handler,
    subscription_check_handler,
)
from app.handlers.search import inline_search_handler, search_pagination_handler, track_action_handler
from app.handlers.download import download_audio_handler, download_video_handler, download_quality_handler
from app.utils.subscription import ensure_music_access


# Initialize services
db_service: DatabaseService = None
redis_service: RedisService = None


async def _cache_cleanup_loop(application: Application) -> None:
    """Periodically clean old cache files in the background."""
    from app.utils.helpers import clean_cache

    interval_seconds = 6 * 60 * 60
    max_age_days = max(1, Config.CACHE_FILE_TTL // 86400)

    while True:
        try:
            deleted_count, freed_size = clean_cache(
                max_age_days=max_age_days,
                max_size_gb=Config.CACHE_MAX_SIZE_GB,
            )
            if deleted_count:
                logger.info(
                    f"Auto cache cleanup: {deleted_count} files removed, {freed_size:.2f} MB freed"
                )
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.warning(f"Auto cache cleanup failed: {e}")

        await asyncio.sleep(interval_seconds)


async def post_init(application: Application) -> None:
    """Initialize application after startup"""
    global db_service, redis_service
    
    logger.info("🚀 Инициализация приложения...")
    application.bot_data["downloader"] = MediaDownloader()
    
    try:
        # Initialize database service
        db_service = DatabaseService(Config.DATABASE_URL)
        await db_service.initialize()
        logger.info("✓ БД инициализирована")
        application.bot_data["db"] = db_service
    except Exception as e:
        logger.warning(f"⚠ БД недоступна (бот работает без неё): {e}")
        application.bot_data["db"] = None
    
    try:
        if Config.REDIS_ENABLED:
            redis_service = RedisService(Config.REDIS_URL)
            await redis_service.initialize()
            logger.info("✓ Redis инициализирован")
            application.bot_data["redis"] = redis_service
            application.bot_data["redis_service"] = redis_service
        else:
            logger.info("ℹ Redis отключен через конфигурацию")
            application.bot_data["redis"] = None
            application.bot_data["redis_service"] = None
    except Exception as e:
        logger.warning(f"⚠ Redis недоступен (бот работает без него): {e}")
        application.bot_data["redis"] = None
        application.bot_data["redis_service"] = None

    application.bot_data["cache_cleanup_task"] = asyncio.create_task(
        _cache_cleanup_loop(application)
    )
    
    logger.info("✓ Приложение готово!")


async def post_stop(application: Application) -> None:
    """Cleanup on application shutdown"""
    logger.info("🛑 Остановка приложения...")
    
    try:
        cleanup_task = application.bot_data.get("cache_cleanup_task")
        if cleanup_task:
            cleanup_task.cancel()
            try:
                await cleanup_task
            except asyncio.CancelledError:
                pass

        if db_service:
            await db_service.close()
        if redis_service:
            await redis_service.close()
        logger.info("✓ Приложение остановлено")
    except Exception as e:
        logger.error(f"✗ Ошибка при остановке: {e}", exc_info=True)


def setup_handlers(application: Application) -> None:
    """Register all bot handlers"""
    
    # Commands
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("search", search_handler))
    application.add_handler(CommandHandler("settings", settings_handler))
    application.add_handler(CommandHandler("queue", queue_handler))
    application.add_handler(CommandHandler("history", history_handler))
    application.add_handler(CommandHandler("favorites", favorites_handler))
    application.add_handler(CommandHandler("popular", popular_handler))
    application.add_handler(CommandHandler("play", play_handler))
    application.add_handler(CommandHandler("skip", skip_handler))
    application.add_handler(CommandHandler("add", queue_add_handler))
    
    # Admin commands
    application.add_handler(CommandHandler("clear_cache", clear_cache_handler))
    
    # Inline search
    application.add_handler(InlineQueryHandler(inline_search_handler))
    
    # Callback buttons - main menu
    application.add_handler(CallbackQueryHandler(menu_callback_handler, pattern="^(search|popular|help|language|currency|referral|recognize)$"))
    
    # Callback buttons - language selection
    application.add_handler(CallbackQueryHandler(language_set_handler, pattern="^set_lang_"))
    application.add_handler(CallbackQueryHandler(subscription_check_handler, pattern="^check_subscription$"))
    application.add_handler(CallbackQueryHandler(settings_callback_handler, pattern="^(audio_quality|video_quality|language_select|set_audio_|set_video_)"))
    
    # Callback buttons - search & download
    application.add_handler(CallbackQueryHandler(search_pagination_handler, pattern="^search_"))
    application.add_handler(CallbackQueryHandler(track_action_handler, pattern="^(listen|favorite)_"))
    application.add_handler(CallbackQueryHandler(handle_url_action, pattern="^(play_url_|dl_url_mp3_|dl_url_mp4_|add_url_)"))
    application.add_handler(CallbackQueryHandler(download_quality_handler, pattern="^quality_"))
    application.add_handler(CallbackQueryHandler(download_audio_handler, pattern="^dl_audio_"))
    application.add_handler(CallbackQueryHandler(download_video_handler, pattern="^dl_video_"))
    
    # Message handlers (last)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice_audio))
    application.add_handler(MessageHandler(filters.ATTACHMENT & ~filters.VOICE & ~filters.AUDIO, handle_attachment))

    # Global error handler
    application.add_error_handler(error_handler)


async def handle_text_message(update, context):
    """Handle text messages (URLs, search queries)"""
    try:
        from app.locales import get_text
        lang = context.user_data.get("lang", "ru")
        text = update.message.text
        
        # Check if it's a URL
        if text.startswith(("http://", "https://", "www.")):
            if not await ensure_music_access(update, context):
                return
            from app.locales import get_text
            import hashlib

            url_hash = hashlib.md5(text.encode()).hexdigest()[:12]
            context.user_data.setdefault("url_actions", {})[url_hash] = text
            await update.message.reply_text(
                get_text("url_detected", lang),
                reply_markup=get_link_action_menu(url_hash)
            )
            return
        
        # If user is awaiting search — treat as search query
        if context.user_data.get("awaiting_search"):
            context.user_data["awaiting_search"] = False
            if not await ensure_music_access(update, context):
                return
            
            from app.handlers.search import send_search_results
            
            wait_msg = await update.message.reply_text(
                get_text("searching", lang, query=text), parse_mode="HTML"
            )
            sent = await send_search_results(wait_msg, context, text, lang)
            if sent:
                logger.info(f"Text search: {text} by {update.effective_user.id}")
            return
        
        # Default — suggest search
        await update.message.reply_text(get_text("default_reply", lang))
    except Exception as e:
        logger.error(f"Error handling text message: {e}")
        await update.message.reply_text(get_text("error", lang, error=str(e)))


async def handle_attachment(update, context):
    """Handle file attachments"""
    try:
        await update.message.reply_text("Отправка файлов не поддерживается. Используй /search для поиска музыки.")
    except Exception as e:
        logger.error(f"Error handling attachment: {e}")


async def handle_voice_audio(update, context):
    """Handle voice messages and audio files for music recognition"""
    import os
    import tempfile
    from app.locales import get_text
    from app.services.downloader import MediaDownloader

    async def _safe_tg_call(coro_factory, retries: int = 3):
        """Retry Telegram API calls on transient network errors."""
        last_exc = None
        for attempt in range(retries):
            try:
                return await coro_factory()
            except (TimedOut, NetworkError) as exc:
                last_exc = exc
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(1.2 * (attempt + 1))
        raise last_exc

    def _normalize(text: str) -> str:
        return " ".join((text or "").lower().replace("-", " ").split())

    def _pick_best_track(candidates: list, expected_artist: str, expected_title: str):
        """Pick most relevant track by similarity and basic quality heuristics."""
        if not candidates:
            return None

        expected = _normalize(f"{expected_artist} {expected_title}")
        expected_artist_norm = _normalize(expected_artist)
        bad_markers = [
            "live", "cover", "karaoke", "nightcore", "sped up", "slowed",
            "8d", "edit", "lyrics", "lyric", "shorts", "tiktok", "remix"
        ]

        best_track = None
        best_score = -999.0

        for tr in candidates:
            title = _normalize(tr.get("title", ""))
            uploader = _normalize(tr.get("uploader", ""))
            duration = tr.get("duration", 0) or 0

            title_score = SequenceMatcher(None, expected, title).ratio()
            artist_score = SequenceMatcher(None, expected_artist_norm, uploader).ratio()
            score = (title_score * 0.8) + (artist_score * 0.2)

            if any(marker in title for marker in bad_markers):
                score -= 0.2
            if "official" in title or "topic" in uploader:
                score += 0.07
            if duration and 90 <= duration <= 360:
                score += 0.05
            elif duration and duration < 45:
                score -= 0.2

            if score > best_score:
                best_score = score
                best_track = tr

        return best_track

    lang = context.user_data.get("lang", "ru")

    if not await ensure_music_access(update, context):
        return

    wait_msg = None

    file_path = None
    try:
        wait_msg = await _safe_tg_call(
            lambda: update.message.reply_text(
                get_text("recognizing", lang), parse_mode="HTML"
            )
        )

        # Download the voice/audio file
        if update.message.voice:
            file = await update.message.voice.get_file()
        else:
            file = await update.message.audio.get_file()

        file_path = os.path.join(tempfile.gettempdir(), f"recognize_{update.effective_user.id}.ogg")
        await file.download_to_drive(file_path)

        from app.services.recognizer import recognize_audio
        result = await recognize_audio(file_path)

        if result:
            extra_parts = []
            if result.get("album"):
                extra_parts.append(f"💿 Альбом: {result['album']}")
            if result.get("genre"):
                extra_parts.append(f"🎶 Жанр: {result['genre']}")
            extra = "\n".join(extra_parts)

            text = get_text(
                "recognize_result", lang,
                artist=result["artist"],
                title=result["title"],
                extra=extra
            )

            await _safe_tg_call(lambda: wait_msg.edit_text(text, parse_mode="HTML"))

            # Auto-search and download the recognized track
            artist = result['artist']
            title = result['title']

            search_msg = await _safe_tg_call(
                lambda: update.message.reply_text(
                    get_text("searching", lang, query=f"{artist} - {title}"), parse_mode="HTML"
                )
            )

            dl = context.bot_data.get("downloader")
            if not dl:
                dl = MediaDownloader()

            # Try multiple search strategies
            search_queries = [
                f"{artist} {title} official audio",
                f"{artist} {title}",
                f"{title} {artist}",
                title,
            ]

            all_candidates = []
            for sq in search_queries:
                search_results = await dl.search(sq, source="youtube", limit=5)
                all_candidates.extend(search_results)

            uniq = {}
            for tr in all_candidates:
                tr_id = tr.get("id")
                if tr_id and tr_id not in uniq:
                    uniq[tr_id] = tr

            best_track = _pick_best_track(list(uniq.values()), artist, title)

            if best_track:
                track = best_track
                track_url = f"https://youtube.com/watch?v={track.get('id', '')}"

                await _safe_tg_call(lambda: search_msg.edit_text(get_text("downloading", lang), parse_mode="HTML"))

                bitrate = context.user_data.get("audio_bitrate", Config.DEFAULT_AUDIO_BITRATE)
                dl_result = await dl.download_audio(track_url, bitrate=bitrate)
                sent = await send_downloaded_audio(
                    update.message,
                    dl_result,
                    lang,
                    status_message=search_msg,
                    tg_call=_safe_tg_call,
                )
                if sent:
                    logger.info(
                        f"Recognized & sent: {dl_result.get('artist', result['artist'])} - {dl_result.get('title', result['title'])}"
                    )
            else:
                await _safe_tg_call(lambda: search_msg.edit_text(get_text("not_found", lang)))
        else:
            if wait_msg:
                await _safe_tg_call(lambda: wait_msg.edit_text(get_text("recognize_fail", lang)))
    except Exception as e:
        logger.error(f"Recognition error: {e}")
        if wait_msg:
            try:
                await _safe_tg_call(lambda: wait_msg.edit_text(get_text("recognize_fail", lang)))
            except Exception:
                pass
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)


async def error_handler(update, context):
    """Global error handler for uncaught exceptions in handlers."""
    logger.error("Unhandled exception", exc_info=context.error)


async def handle_url_action(update, context):
    """Handle actions for direct URL messages using stored short tokens."""
    query = update.callback_query
    await query.answer()

    if not await ensure_music_access(update, context):
        return

    from app.locales import get_text
    lang = context.user_data.get("lang", "ru")
    data = query.data

    action = None
    url_hash = None
    if data.startswith("play_url_"):
        action = "play_url"
        url_hash = data.replace("play_url_", "", 1)
    elif data.startswith("dl_url_mp3_"):
        action = "dl_url_mp3"
        url_hash = data.replace("dl_url_mp3_", "", 1)
    elif data.startswith("dl_url_mp4_"):
        action = "dl_url_mp4"
        url_hash = data.replace("dl_url_mp4_", "", 1)
    elif data.startswith("add_url_"):
        action = "add_url"
        url_hash = data.replace("add_url_", "", 1)

    if not action or not url_hash:
        await query.message.reply_text(get_text("invalid_callback_data", lang))
        return

    url = context.user_data.get("url_actions", {}).get(url_hash)
    if not url:
        await query.message.reply_text(get_text("url_invalid", lang))
        return

    dl = context.bot_data.get("downloader") or MediaDownloader()
    bitrate = context.user_data.get("audio_bitrate", Config.DEFAULT_AUDIO_BITRATE)
    resolution = context.user_data.get("video_resolution", Config.DEFAULT_VIDEO_RESOLUTION)

    if action in {"play_url", "dl_url_mp3", "dl_url_mp4"}:
        if action == "dl_url_mp4":
            status_msg = await query.message.reply_text(get_text("downloading", lang), parse_mode="HTML")
            result_path = await dl.download_video(url, resolution=resolution)
            from app.utils.media_delivery import send_downloaded_video
            await send_downloaded_video(query.message, result_path, lang, status_message=status_msg)
            return

        status_msg = await query.message.reply_text(get_text("downloading", lang), parse_mode="HTML")
        result = await dl.download_audio(url, bitrate=bitrate)
        from app.utils.media_delivery import send_downloaded_audio
        await send_downloaded_audio(query.message, result, lang, status_message=status_msg)
        return

    if action == "add_url":
        queue = context.user_data.setdefault("url_queue", [])
        queue.append(url)
        await query.message.reply_text(get_text("url_added_to_queue", lang))
        return

    await query.message.reply_text(get_text("invalid_callback_data", lang))


def get_link_action_menu(url_hash: str):
    """Get inline keyboard for URL actions"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [
            InlineKeyboardButton("🎧 Слушать", callback_data=f"play_url_{url_hash}"),
            InlineKeyboardButton("📱 MP3", callback_data=f"dl_url_mp3_{url_hash}"),
        ],
        [
            InlineKeyboardButton("🎬 MP4", callback_data=f"dl_url_mp4_{url_hash}"),
            InlineKeyboardButton("➕ В очередь", callback_data=f"add_url_{url_hash}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def main() -> None:
    """Run the bot"""
    
    # Setup logging
    setup_logging(Config.LOG_FILE, Config.LOG_LEVEL)
    
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return
    
    logger.info(f"🎵 Запуск {Config.APP_NAME}...")

    builder = Application.builder().token(Config.BOT_TOKEN)

    # Use an explicit HTTP client only when proxy behavior is requested.
    # The default PTB request client is more stable on this Windows environment.
    if Config.TELEGRAM_PROXY_URL or Config.TELEGRAM_USE_ENV_PROXY:
        proxy = Config.TELEGRAM_PROXY_URL if Config.TELEGRAM_PROXY_URL else None
        request_kwargs = {
            "connect_timeout": Config.TELEGRAM_CONNECT_TIMEOUT,
            "read_timeout": Config.TELEGRAM_READ_TIMEOUT,
            "write_timeout": Config.TELEGRAM_WRITE_TIMEOUT,
            "pool_timeout": Config.TELEGRAM_POOL_TIMEOUT,
            "media_write_timeout": Config.TELEGRAM_MEDIA_WRITE_TIMEOUT,
            "http_version": "1.1",
            "proxy": proxy,
            "httpx_kwargs": {"trust_env": Config.TELEGRAM_USE_ENV_PROXY},
        }

        bot_request = HTTPXRequest(connection_pool_size=20, **request_kwargs)
        get_updates_request = HTTPXRequest(connection_pool_size=2, **request_kwargs)
        builder = builder.request(bot_request).get_updates_request(get_updates_request)

    # Create application
    application = builder.build()
    
    # Set up handlers
    setup_handlers(application)
    
    # Set up initialization and shutdown
    application.post_init = post_init
    application.post_stop = post_stop
    
    # Run bot
    try:
        application.run_polling(
            allowed_updates=["message", "callback_query", "inline_query"],
            bootstrap_retries=Config.TELEGRAM_BOOTSTRAP_RETRIES,
        )
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
