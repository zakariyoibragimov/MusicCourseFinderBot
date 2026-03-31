"""
Main application file for Telegram music bot
Initializes all handlers, services, and runs the bot
"""

import asyncio
import hashlib
import os
import re
from difflib import SequenceMatcher
from pathlib import Path
from telegram.error import TimedOut, NetworkError
from telegram.request import HTTPXRequest
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    InlineQueryHandler, CallbackQueryHandler
)

from app.config import Config
from app.locales import get_text
from app.utils.helpers import clean_cache
from app.utils.logger import setup_logging, logger
from app.utils.telegram_helpers import safe_answer_callback
from app.services.database import DatabaseService
from app.services.downloader import MediaDownloader
from app.services.redis_service import RedisService
from app.handlers.commands import (
    start_handler, help_handler, search_handler, settings_handler,
    queue_handler, history_handler, favorites_handler, popular_handler,
    clear_cache_handler,
    play_handler, skip_handler, queue_add_handler,
    menu_callback_handler, language_set_handler, settings_callback_handler,
    subscription_check_handler, reset_user_flow_state,
)
from app.handlers.search import inline_search_handler, search_pagination_handler, track_action_handler
from app.handlers.download import download_audio_handler, download_video_handler, download_quality_handler
from app.utils.media_delivery import send_downloaded_audio
from app.utils.subscription import ensure_music_access

try:
    import msvcrt
except ImportError:
    msvcrt = None

try:
    import fcntl
except ImportError:
    fcntl = None


if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


# Initialize services
db_service: DatabaseService = None
redis_service: RedisService = None
instance_lock_file = None


def acquire_instance_lock() -> bool:
    """Prevent multiple local bot instances from polling Telegram at the same time."""
    global instance_lock_file

    if instance_lock_file is not None:
        return True

    lock_path = Path(Config.CACHE_DIR) / "bot.instance.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    lock_file = open(lock_path, "a+")
    lock_file.seek(0)
    lock_file.write("0")
    lock_file.flush()
    lock_file.seek(0)

    try:
        if msvcrt is not None:
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        elif fcntl is not None:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        lock_file.close()
        return False

    lock_file.seek(0)
    lock_file.truncate()
    lock_file.write(str(os.getpid()))
    lock_file.flush()
    instance_lock_file = lock_file
    return True


def release_instance_lock() -> None:
    """Release the local single-instance lock."""
    global instance_lock_file

    if instance_lock_file is None:
        return

    try:
        instance_lock_file.seek(0)
        if msvcrt is not None:
            msvcrt.locking(instance_lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        elif fcntl is not None:
            fcntl.flock(instance_lock_file.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass
    finally:
        instance_lock_file.close()
        instance_lock_file = None


async def _cache_cleanup_loop(application: Application) -> None:
    """Periodically clean old cache files in the background."""
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
    # Popular pagination
    from app.handlers.commands import popular_pagination_handler
    application.add_handler(CallbackQueryHandler(popular_pagination_handler, pattern="^popular_(next|prev)_"))
    
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
        lang = context.user_data.get("lang", "ru")
        text = update.message.text

        if context.user_data.get("awaiting_audio"):
            await update.message.reply_text(get_text("recognize_prompt", lang), parse_mode="HTML")
            return
        
        # Check if it's a URL
        if text.startswith(("http://", "https://", "www.")):
            if not await ensure_music_access(update, context):
                return
            reset_user_flow_state(context)

            url_hash = hashlib.md5(text.encode()).hexdigest()[:12]
            context.user_data.setdefault("url_actions", {})[url_hash] = text
            await update.message.reply_text(
                get_text("url_detected", lang),
                reply_markup=get_link_action_menu(url_hash)
            )
            return
        
        # If user is awaiting search — treat as search query
        if context.user_data.get("awaiting_search"):
            reset_user_flow_state(context)
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


def _normalize_music_text(value: str) -> str:
    normalized = (value or "").lower().replace("ё", "е")
    normalized = re.sub(r"[^\w\s]+", " ", normalized, flags=re.UNICODE)
    normalized = re.sub(r"\s+", " ", normalized, flags=re.UNICODE)
    return normalized.strip()


def _text_similarity(left: str, right: str) -> float:
    left_norm = _normalize_music_text(left)
    right_norm = _normalize_music_text(right)
    if not left_norm or not right_norm:
        return 0.0
    if left_norm == right_norm:
        return 1.0
    return SequenceMatcher(None, left_norm, right_norm).ratio()


def _score_recognition_candidate(recognized: dict, candidate: dict) -> float:
    title = recognized.get("title", "")
    artist = recognized.get("artist", "")
    candidate_title = candidate.get("title", "")
    candidate_artist = candidate.get("uploader", "")
    combined_candidate = f"{candidate_title} {candidate_artist}"

    title_score = _text_similarity(title, candidate_title)
    artist_score = _text_similarity(artist, candidate_artist)
    combined_score = _text_similarity(f"{artist} {title}", combined_candidate)

    score = (title_score * 0.5) + (artist_score * 0.35) + (combined_score * 0.15)

    markers = ["live", "cover", "remix", "karaoke", "instrumental", "shorts", "sped up", "slowed"]
    lowered = _normalize_music_text(combined_candidate)
    if any(marker in lowered for marker in markers):
        score -= 0.2

    duration = candidate.get("duration")
    if isinstance(duration, (int, float)):
        if duration < 45:
            score -= 0.3
        elif duration > 480:
            score -= 0.15

    return score


def _get_downloader(context) -> MediaDownloader:
    """Get the shared downloader service with a safe local fallback."""
    return context.bot_data.get("downloader") or MediaDownloader()


async def _find_best_recognized_track(context, recognized: dict) -> dict | None:
    query = " ".join(part for part in [recognized.get("artist"), recognized.get("title")] if part)
    if not query:
        return None

    downloader = _get_downloader(context)
    candidates = await downloader.search(query, source="youtube", limit=10)
    if not candidates:
        return None

    ranked = sorted(candidates, key=lambda item: _score_recognition_candidate(recognized, item), reverse=True)
    best_candidate = ranked[0]
    if _score_recognition_candidate(recognized, best_candidate) < 0.45:
        return None
    return best_candidate


async def handle_voice_audio(update, context):
    """Handle voice messages and audio files for music recognition"""
    import os
    import tempfile

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

    lang = context.user_data.get("lang", "ru")

    if not await ensure_music_access(update, context):
        return

    reset_user_flow_state(context)

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
            best_track = await _find_best_recognized_track(context, result)
            if not best_track:
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
                await _safe_tg_call(lambda: wait_msg.edit_text(text, parse_mode="HTML", disable_web_page_preview=True))
                return

            await _safe_tg_call(lambda: wait_msg.edit_text(get_text("downloading", lang), parse_mode="HTML"))

            downloader = _get_downloader(context)
            bitrate = context.user_data.get("audio_bitrate", Config.DEFAULT_AUDIO_BITRATE)
            audio_result = await downloader.download_audio(best_track.get("url") or f"https://youtube.com/watch?v={best_track.get('id')}", bitrate=bitrate)
            if audio_result:
                audio_result["title"] = result.get("title") or audio_result.get("title")
                audio_result["artist"] = result.get("artist") or audio_result.get("artist")

            sent = await send_downloaded_audio(
                update.message,
                audio_result,
                lang,
                status_message=wait_msg,
                tg_call=_safe_tg_call,
            )
            if sent:
                logger.info(
                    f"Recognized and sent MP3 for user {update.effective_user.id}: {result['artist']} - {result['title']}"
                )
            else:
                await _safe_tg_call(lambda: wait_msg.edit_text(get_text("download_fail", lang)))
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
    await safe_answer_callback(query)

    try:
        if not await ensure_music_access(update, context):
            return

        reset_user_flow_state(context)
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

        dl = _get_downloader(context)
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
            db = context.bot_data.get("db")
            if not db:
                await query.message.reply_text(get_text("queue_db_unavailable", lang))
                return

            title = url if len(url) <= 60 else f"{url[:57]}..."
            await db.add_to_queue(
                update.effective_user.id,
                {
                    "id": url_hash,
                    "title": title,
                    "url": url,
                    "source": "direct_url",
                    "duration": 0,
                },
            )
            await query.message.reply_text(get_text("url_added_to_queue", lang))
            return

        await query.message.reply_text(get_text("invalid_callback_data", lang))
    except Exception as error:
        logger.error(f"URL action error: {error}")
        lang = context.user_data.get("lang", "ru")
        await query.message.reply_text(get_text("download_fail", lang))


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

    if not acquire_instance_lock():
        logger.error("Another bot instance is already running; aborting duplicate start")
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
            "proxy": proxy,
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
    finally:
        release_instance_lock()


if __name__ == "__main__":
    main()
