"""
Basic command handlers for the bot
/start, /help, /search, /settings, /queue, /history, /favorites, /popular, /play, /skip, /add, /clear_cache
"""

from functools import wraps
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.utils.logger import logger
from app.utils.rate_limiter import rate_limiter
from app.config import Config
from app.services.downloader import MediaDownloader
from app.locales import get_text
from app.utils.subscription import ensure_music_access, get_free_usage_count, get_subscription_markup, is_user_subscribed
import hashlib
from sqlalchemy import select, func


LANGUAGE_CHOICES = [
    ("🇷🇺 Русский", "ru"),
    ("🇬🇧 English", "en"),
    ("🇹🇯 Тоҷикӣ", "tg"),
    ("🇺🇿 O'zbekcha", "uz"),
]

POPULAR_LANGUAGE_QUERIES = [
    ("tajik", ["сурудхои точики 2025", "tajik songs 2025", "tojik music 2025"], 6),
    ("uzbek", ["uzbek qo'shiqlari 2025", "узбек музыка 2025", "uzbek songs 2025"], 6),
    ("russian", ["русские хиты 2025", "русская музыка новинки 2025", "russian songs 2025"], 4),
    ("english", ["english pop hits 2025", "top english songs 2025", "new english songs 2025"], 4),
]

POPULAR_TRACK_LIMIT = 20


def _get_lang(context) -> str:
    """Get user's language from context."""
    return context.user_data.get("lang", "ru")


def _get_help_markup(lang: str):
    """Build help keyboard with operator contact."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(get_text("btn_operator_1", lang), url="https://t.me/MLiv328"),
            InlineKeyboardButton(get_text("btn_operator_2", lang), url="https://t.me/Isengard97"),
        ]
    ])


def _get_main_menu_markup(lang: str) -> InlineKeyboardMarkup:
    """Build the main menu keyboard shown after /start and language change."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(get_text("btn_search", lang), callback_data="search"),
            InlineKeyboardButton(get_text("btn_popular", lang), callback_data="popular"),
        ],
        [
            InlineKeyboardButton(get_text("btn_recognize", lang), callback_data="recognize"),
            InlineKeyboardButton(get_text("btn_currency", lang), callback_data="currency"),
        ],
        [
            InlineKeyboardButton(get_text("btn_referral", lang), callback_data="referral"),
            InlineKeyboardButton(get_text("btn_language", lang), callback_data="language"),
        ],
        [
            InlineKeyboardButton(get_text("btn_help", lang), callback_data="help"),
        ],
    ])


def _get_language_markup() -> InlineKeyboardMarkup:
    """Build language selection keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(label, callback_data=f"set_lang_{lang_code}")]
        for label, lang_code in LANGUAGE_CHOICES
    ])


def _format_duration(duration) -> str:
    """Format duration in seconds as MM:SS."""
    try:
        total_seconds = int(duration or 0)
    except (TypeError, ValueError):
        return "--:--"

    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d}"


def _trim_title(title: str, limit: int = 42) -> str:
    """Trim long titles for compact chat output."""
    if not title:
        return "Unknown"
    return title if len(title) <= limit else f"{title[:limit - 1]}..."


def _build_track_list_keyboard(results: list, refresh_label: str | None = None, refresh_callback: str = "popular") -> InlineKeyboardMarkup:
    """Build a simple one-button-per-track keyboard with optional refresh row."""
    keyboard = []

    for idx, track in enumerate(results, 1):
        title = _trim_title(track.get("title", "Unknown"), limit=35)
        duration = track.get("duration", 0)
        duration_suffix = ""
        if isinstance(duration, (int, float)) and duration > 0:
            duration_suffix = f" ({_format_duration(duration)})"

        track_id = track.get("id", str(idx))
        keyboard.append([
            InlineKeyboardButton(
                f"▶️ {idx}. {title}{duration_suffix}",
                callback_data=f"listen_{track_id}",
            ),
        ])

    if refresh_label:
        keyboard.append([InlineKeyboardButton(refresh_label, callback_data=refresh_callback)])

    return InlineKeyboardMarkup(keyboard)


def _build_popular_reply(results: list, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """Format popular tracks text and keyboard in one place."""
    reply_markup = _build_track_list_keyboard(results[:POPULAR_TRACK_LIMIT], refresh_label=get_text("btn_refresh", lang))
    return get_text("popular_title", lang), reply_markup


async def _load_popular_tracks(context, limit: int = POPULAR_TRACK_LIMIT) -> list:
    """Load popular tracks ordered by language groups: Tajik, Uzbek, Russian, English."""
    downloader = context.bot_data.get("downloader")
    if not downloader:
        downloader = MediaDownloader()

    results = []
    seen_ids = set()

    for _, queries, target_count in POPULAR_LANGUAGE_QUERIES:
        added_for_group = 0

        for query in queries:
            search_results = await downloader.search(query, source="youtube", limit=max(target_count * 2, target_count))

            for track in search_results:
                track_id = track.get("id")
                if not track_id or track_id in seen_ids:
                    continue

                seen_ids.add(track_id)
                results.append(track)
                added_for_group += 1

                if len(results) >= limit or added_for_group >= target_count:
                    break

            if len(results) >= limit or added_for_group >= target_count:
                break

        if len(results) >= limit:
            break

    return results[:limit]


def admin_only(func):
    """Decorator to check if user is admin"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_user.id != Config.ADMIN_ID:
            await update.message.reply_text("❌ Эта команда доступна только администратору")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    
    if not rate_limiter.is_allowed(update.effective_user.id):
        await update.message.reply_text("⏳ Вы отправляете слишком много запросов. Попробуйте позже")
        return
    
    user = update.effective_user
    lang = _get_lang(context)
    
    # Handle referral deep link: /start ref_12345
    if context.args and context.args[0].startswith("ref_"):
        try:
            referrer_id = int(context.args[0][4:])
            if referrer_id != user.id:
                await _process_referral(referrer_id, user.id, context)
                await update.message.reply_text(
                    get_text("referral_welcome", lang), parse_mode="HTML"
                )
        except (ValueError, Exception) as e:
            logger.warning(f"Invalid referral link: {e}")
    
    reply_markup = _get_main_menu_markup(lang)
    text = get_text("welcome", lang, app_name=Config.APP_NAME, name=user.first_name)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")
    subscribed = await is_user_subscribed(context, user.id)
    if subscribed is not True:
        used_count = await get_free_usage_count(context, user)
        remaining = max(0, Config.FREE_MUSIC_REQUEST_LIMIT - used_count)
        await update.message.reply_text(
            get_text(
                "subscription_required" if subscribed is False else "subscription_check_failed",
                lang,
                channel=Config.REQUIRED_CHANNEL_USERNAME,
                limit=Config.FREE_MUSIC_REQUEST_LIMIT,
                remaining=remaining,
            ),
            parse_mode="HTML",
            reply_markup=get_subscription_markup(lang),
        )
    logger.info(f"User started bot: {user.username} ({user.id})")


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    
    lang = _get_lang(context)
    await update.message.reply_text(
        get_text("help_text", lang),
        parse_mode="HTML",
        reply_markup=_get_help_markup(lang),
    )


async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /search command"""
    if not await ensure_music_access(update, context):
        return

    if not context.args:
        await update.message.reply_text("🔍 <b>Использование:</b> /search &lt;запрос&gt;", parse_mode="HTML")
        return
    
    query = " ".join(context.args)
    
    if not rate_limiter.is_allowed(update.effective_user.id):
        retry_after = rate_limiter.get_retry_after(update.effective_user.id)
        await update.message.reply_text(f"⏳ Слишком много запросов. Попробуй через {retry_after} сек")
        return

    from app.handlers.search import send_search_results

    wait_msg = await update.message.reply_text(f"🔍 <b>Ищу:</b> {query}...", parse_mode="HTML")

    try:
        sent = await send_search_results(wait_msg, context, query, _get_lang(context))
        if sent:
            logger.info(f"Search: {query} by {update.effective_user.id}")
    except Exception as e:
        logger.error(f"Search command error: {e}")
        await wait_msg.edit_text(f"❌ Ошибка: {str(e)}")


async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /settings command"""
    lang = _get_lang(context)
    
    keyboard = [
        [
            InlineKeyboardButton(get_text("settings_audio", lang), callback_data="audio_quality"),
            InlineKeyboardButton(get_text("settings_video", lang), callback_data="video_quality")
        ],
        [
            InlineKeyboardButton(get_text("settings_language", lang), callback_data="language_select"),
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(get_text("settings_title", lang), reply_markup=reply_markup, parse_mode="HTML")


async def _save_user_preferences(context, user, **fields) -> None:
    """Persist user preferences to DB when available and keep them in user_data."""
    context.user_data.update(fields)

    db = context.bot_data.get("db")
    if not db:
        return

    try:
        from app.services.database import User

        session = await db.get_session()
        async with session:
            result = await session.execute(select(User).where(User.user_id == user.id))
            db_user = result.scalar_one_or_none()
            if not db_user:
                db_user = User(
                    user_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    language=context.user_data.get("lang", "ru"),
                    audio_bitrate=context.user_data.get("audio_bitrate", Config.DEFAULT_AUDIO_BITRATE),
                    video_resolution=context.user_data.get("video_resolution", Config.DEFAULT_VIDEO_RESOLUTION),
                )
                session.add(db_user)

            for key, value in fields.items():
                if hasattr(db_user, key):
                    setattr(db_user, key, value)

            await session.commit()
    except Exception as e:
        logger.error(f"Failed to save user preferences: {e}")


async def settings_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle settings-related callbacks."""
    query = update.callback_query
    await query.answer()
    lang = _get_lang(context)
    data = query.data

    if data == "audio_quality":
        keyboard = [
            [InlineKeyboardButton(f"{bitrate} kbps", callback_data=f"set_audio_{bitrate}")]
            for bitrate in Config.SUPPORTED_AUDIO_BITRATES
        ]
        await query.message.reply_text(
            get_text("settings_audio_choose", lang),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return

    if data == "video_quality":
        keyboard = [
            [InlineKeyboardButton(f"{resolution}p", callback_data=f"set_video_{resolution}")]
            for resolution in Config.SUPPORTED_VIDEO_RESOLUTIONS
        ]
        await query.message.reply_text(
            get_text("settings_video_choose", lang),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return

    if data == "language_select":
        await query.message.reply_text(
            get_text("choose_language", lang),
            reply_markup=_get_language_markup(),
            parse_mode="HTML",
        )
        return

    if data.startswith("set_audio_"):
        bitrate = data.replace("set_audio_", "")
        await _save_user_preferences(context, update.effective_user, audio_bitrate=bitrate)
        await query.message.reply_text(get_text("settings_audio_saved", lang, value=bitrate), parse_mode="HTML")
        return

    if data.startswith("set_video_"):
        resolution = data.replace("set_video_", "")
        await _save_user_preferences(context, update.effective_user, video_resolution=resolution)
        await query.message.reply_text(get_text("settings_video_saved", lang, value=resolution), parse_mode="HTML")
        return


async def queue_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /queue command"""
    db = context.bot_data.get("db")
    if not db:
        await update.message.reply_text("❌ База данных недоступна. Очередь временно отключена.")
        return

    try:
        queue_items = await db.get_user_queue(update.effective_user.id, limit=15)
        if not queue_items:
            text = (
                "🎵 <b>Ваша очередь пуста</b>\n\n"
                "Сначала найди музыку через /search, потом добавь трек командой /add 1"
            )
            await update.message.reply_text(text, parse_mode="HTML")
            return

        lines = ["🎵 <b>Ваша очередь</b>", ""]
        for item in queue_items:
            lines.append(f"<b>{item.position}. {_trim_title(item.title)}</b>")
            lines.append(f"• ⏱️ {_format_duration(item.duration)}")
            if item.source:
                lines.append(f"• Источник: {item.source}")
            lines.append("")

        await update.message.reply_text("\n".join(lines).strip(), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Queue handler error: {e}")
        await update.message.reply_text(f"❌ Ошибка очереди: {str(e)}")


async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /history command"""
    db = context.bot_data.get("db")
    if not db:
        await update.message.reply_text("❌ База данных недоступна. История временно отключена.")
        return

    try:
        history_items = await db.get_user_history(update.effective_user.id, limit=10)
        if not history_items:
            text = (
                "📜 <b>История</b>\n\n"
                "У вас пока нет истории прослушивания. Найди трек и нажми кнопку прослушивания."
            )
            await update.message.reply_text(text, parse_mode="HTML")
            return

        lines = ["📜 <b>История</b>", ""]
        for index, item in enumerate(history_items, 1):
            action = item.action or "listened"
            lines.append(f"<b>{index}. {_trim_title(item.title)}</b>")
            lines.append(f"• Действие: {action}")
            lines.append(f"• ⏱️ {_format_duration(item.duration)}")
            lines.append(f"• {item.accessed_at.strftime('%d.%m %H:%M')}")
            lines.append("")

        await update.message.reply_text("\n".join(lines).strip(), parse_mode="HTML")
    except Exception as e:
        logger.error(f"History handler error: {e}")
        await update.message.reply_text(f"❌ Ошибка истории: {str(e)}")


async def favorites_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /favorites command"""
    db = context.bot_data.get("db")
    if not db:
        await update.message.reply_text("❌ База данных недоступна. Избранное временно отключено.")
        return

    try:
        favorite_items = await db.get_user_favorites(update.effective_user.id, limit=15)
        if not favorite_items:
            text = (
                "❤️ <b>Избранное</b>\n\n"
                "Избранное пока пусто. Нажимай ❤️ возле найденных треков, чтобы сохранить их."
            )
            await update.message.reply_text(text, parse_mode="HTML")
            return

        lines = ["❤️ <b>Избранное</b>", ""]
        for index, item in enumerate(favorite_items, 1):
            lines.append(f"<b>{index}. {_trim_title(item.title)}</b>")
            lines.append(f"• ⏱️ {_format_duration(item.duration)}")
            if item.source:
                lines.append(f"• Источник: {item.source}")
            lines.append("")

        await update.message.reply_text("\n".join(lines).strip(), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Favorites handler error: {e}")
        await update.message.reply_text(f"❌ Ошибка избранного: {str(e)}")


async def popular_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /popular command - shows real popular tracks"""
    if not await ensure_music_access(update, context):
        return
    
    wait_msg = await update.message.reply_text("🔥 <b>Загружаю популярные треки...</b>", parse_mode="HTML")
    
    try:
        results = await _load_popular_tracks(context, limit=POPULAR_TRACK_LIMIT)
        
        if not results:
            await wait_msg.edit_text("❌ Не удалось загрузить популярные треки")
            return
        
        from app.handlers.search import store_search_results

        query_hash = store_search_results(context, "popular_music", results)
        
        text, reply_markup = _build_popular_reply(results, _get_lang(context))
        
        await wait_msg.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
        logger.info(f"Popular tracks loaded in language order for {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"Popular handler error: {e}")
        await wait_msg.edit_text(f"❌ Ошибка: {str(e)}")


@admin_only
async def clear_cache_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /clear_cache command (admin only)"""
    
    from app.utils.helpers import clean_cache, get_cache_size_gb
    
    text = "🧹 Очищаю кэш..."
    msg = await update.message.reply_text(text)
    
    try:
        size_before = get_cache_size_gb()
        deleted_count, freed_size = clean_cache(max_age_days=7)
        size_after = get_cache_size_gb()
        
        text = f"""
✓ <b>Кэш очищен</b>

📊 Статистика:
  • Удалено файлов: {deleted_count}
  • Освобождено: {freed_size:.2f} МБ
  • Было: {size_before:.2f} ГБ
  • Стало: {size_after:.2f} ГБ
"""
        
        await msg.edit_text(text, parse_mode="HTML")
        logger.info(f"Cache cleared: {deleted_count} files, {freed_size:.2f} MB freed")
        
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка: {str(e)}")
        logger.error(f"Cache clear error: {e}")


async def play_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /play command"""
    
    text = "🎧 Воспроизведение начнется с первого трека в очереди"
    await update.message.reply_text(text)


async def skip_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /skip command"""
    
    text = "⏭️ Переключение на следующий трек..."
    await update.message.reply_text(text)


async def queue_add_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /add command"""
    if not context.args:
        text = "Использование: /add &lt;номер трека&gt;"
        await update.message.reply_text(text, parse_mode="HTML")
        return

    try:
        from app.handlers.search import get_last_search_results

        track_num = int(context.args[0])
        db = context.bot_data.get("db")
        if not db:
            await update.message.reply_text("❌ База данных недоступна. Добавление в очередь временно отключено.")
            return

        results = get_last_search_results(context)
        if not results:
            await update.message.reply_text("❌ Сначала выполни поиск или открой популярные треки, потом используй /add.")
            return

        if track_num < 1 or track_num > len(results):
            await update.message.reply_text(f"❌ Доступны номера от 1 до {len(results)}")
            return

        track = results[track_num - 1]
        position = await db.add_to_queue(update.effective_user.id, track)
        title = _trim_title(track.get("title", "Unknown"), limit=60)
        text = f"➕ <b>{title}</b> добавлен в очередь под номером {position}"
        await update.message.reply_text(text, parse_mode="HTML")
    except (ValueError, IndexError):
        text = "❌ Укажи правильный номер трека"
        await update.message.reply_text(text)
    except Exception as e:
        logger.error(f"Queue add error: {e}")
        await update.message.reply_text(f"❌ Ошибка добавления в очередь: {str(e)}")


async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle main menu button callbacks from /start"""
    
    query = update.callback_query
    await query.answer()
    
    action = query.data
    user = update.effective_user
    lang = _get_lang(context)
    
    if action == "search":
        context.user_data["awaiting_search"] = True
        await query.message.reply_text(
            get_text("search_prompt", lang),
            parse_mode="HTML"
        )
    
    elif action == "popular":
        if not await ensure_music_access(update, context):
            return
        await query.message.reply_text(get_text("loading_popular", lang), parse_mode="HTML")
        
        try:
            results = await _load_popular_tracks(context, limit=POPULAR_TRACK_LIMIT)
            
            if not results:
                await query.message.reply_text(get_text("popular_error", lang))
            else:
                from app.handlers.search import store_search_results

                query_hash = store_search_results(context, "popular_music", results)
                
                text, reply_markup = _build_popular_reply(results, lang)
                await query.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")
                logger.info(f"Popular menu loaded in language order for {user.id}")
                
        except Exception as e:
            logger.error(f"Popular menu error: {e}")
            await query.message.reply_text(f"❌ Ошибка: {str(e)}")
    
    elif action == "currency":
        await query.message.reply_text(get_text("currency_loading", lang), parse_mode="HTML")
        try:
            from app.services.currency import get_exchange_rates, format_currency_message, LANG_CURRENCIES
            base = LANG_CURRENCIES.get(lang, "USD")
            rates = await get_exchange_rates(base)
            if rates:
                text = format_currency_message(rates, base, lang)
                await query.message.reply_text(text, parse_mode="HTML")
            else:
                await query.message.reply_text(get_text("currency_error", lang))
        except Exception as e:
            logger.error(f"Currency error: {e}")
            await query.message.reply_text(get_text("currency_error", lang))
    
    elif action == "language":
        await query.message.reply_text(
            get_text("choose_language", lang), reply_markup=_get_language_markup(), parse_mode="HTML"
        )
    
    elif action == "help":
        await query.message.reply_text(
            get_text("help_text", lang),
            parse_mode="HTML",
            reply_markup=_get_help_markup(lang),
        )
    
    elif action == "recognize":
        if not await ensure_music_access(update, context):
            return
        context.user_data["awaiting_audio"] = True
        await query.message.reply_text(
            get_text("recognize_prompt", lang), parse_mode="HTML"
        )
    
    elif action == "referral":
        await _show_referral_stats(query.message, user.id, lang, context)
    
    logger.info(f"Menu action '{action}' by {user.username} ({user.id})")


async def language_set_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle language selection buttons."""
    query = update.callback_query
    await query.answer()
    
    chosen = query.data.replace("set_lang_", "")
    context.user_data["lang"] = chosen
    await _save_user_preferences(context, update.effective_user, language=chosen)
    lang = chosen
    
    # Show confirmation + main menu
    user = update.effective_user
    reply_markup = _get_main_menu_markup(lang)
    
    text = get_text("language_set", lang) + "\n\n" + get_text("welcome", lang, app_name=Config.APP_NAME, name=user.first_name)
    await query.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")


async def subscription_check_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Re-check channel subscription status when user presses the button."""
    query = update.callback_query
    await query.answer()

    lang = _get_lang(context)
    subscribed = await is_user_subscribed(context, update.effective_user.id)
    if subscribed is True:
        await query.message.reply_text(get_text("subscription_verified", lang), parse_mode="HTML")
        return

    used_count = await get_free_usage_count(context, update.effective_user)
    remaining = max(0, Config.FREE_MUSIC_REQUEST_LIMIT - used_count)
    key = "subscription_not_verified" if subscribed is False else "subscription_check_failed"
    await query.message.reply_text(
        get_text(key, lang, channel=Config.REQUIRED_CHANNEL_USERNAME, limit=Config.FREE_MUSIC_REQUEST_LIMIT, remaining=remaining),
        parse_mode="HTML",
        reply_markup=get_subscription_markup(lang),
    )


async def _process_referral(referrer_id: int, referred_id: int, context) -> None:
    """Save referral to database."""
    db = context.bot_data.get("db")
    if not db:
        return
    try:
        from app.services.database import Referral
        session = await db.get_session()
        async with session:
            # Check if already referred
            existing = await session.execute(
                select(Referral).where(Referral.referred_id == referred_id)
            )
            if existing.scalar_one_or_none():
                return
            referral = Referral(referrer_id=referrer_id, referred_id=referred_id)
            session.add(referral)
            await session.commit()

            # Notify referrer
            count_result = await session.execute(
                select(func.count()).where(Referral.referrer_id == referrer_id)
            )
            count = count_result.scalar()
            lang = context.user_data.get("lang", "ru")
            try:
                await context.bot.send_message(
                    referrer_id,
                    get_text("referral_new", lang, count=count),
                    parse_mode="HTML"
                )
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Referral save error: {e}")


async def _show_referral_stats(message, user_id: int, lang: str, context) -> None:
    """Show referral stats and link."""
    bot_info = await context.bot.get_me()
    link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"

    count = 0
    db = context.bot_data.get("db")
    if db:
        try:
            from app.services.database import Referral
            session = await db.get_session()
            async with session:
                result = await session.execute(
                    select(func.count()).where(Referral.referrer_id == user_id)
                )
                count = result.scalar()
        except Exception as e:
            logger.error(f"Referral stats error: {e}")

    text = get_text("referral_stats", lang, count=count, link=link)
    await message.reply_text(text, parse_mode="HTML")

