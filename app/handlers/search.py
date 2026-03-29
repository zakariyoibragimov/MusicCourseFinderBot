"""
Search handlers for inline search and search results pagination
"""

from telegram import Update, InlineQuery, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.utils.logger import logger
from app.services.downloader import MediaDownloader
from app.utils.media_delivery import send_downloaded_audio
from app.locales import get_text
from app.utils.subscription import ensure_music_access
import uuid
import hashlib


def store_search_results(context, query_text: str, results: list) -> str:
    """Store search results for pagination and follow-up actions like /add."""
    query_hash = hashlib.md5(query_text.encode()).hexdigest()[:8]
    storage_key = f'search_results_{query_hash}'
    context.user_data[storage_key] = results
    context.user_data["last_search_results_key"] = storage_key
    context.user_data["last_search_results"] = results
    context.user_data["last_search_query"] = query_text
    return query_hash


def get_last_search_results(context) -> list:
    """Get last stored search results from context."""
    last_results = context.user_data.get("last_search_results")
    if last_results:
        return last_results

    storage_key = context.user_data.get("last_search_results_key")
    if storage_key:
        return context.user_data.get(storage_key, [])

    return []


def get_track_from_results(context, track_id: str):
    """Find track by id inside the latest stored search results."""
    for track in get_last_search_results(context):
        if str(track.get("id")) == str(track_id):
            return track
    return None


async def send_search_results(wait_message, context, query_text: str, lang: str) -> bool:
    """Search YouTube and replace a waiting message with formatted results."""
    downloader = context.bot_data.get("downloader")
    if not downloader:
        downloader = MediaDownloader()

    results = await downloader.search(query_text, source="youtube", limit=10)
    if not results:
        await wait_message.edit_text(get_text("not_found", lang))
        return False

    query_hash = store_search_results(context, query_text, results)
    result_text = await _format_search_results(results, 0, query_text)
    keyboard = await _get_search_keyboard(results, 0, query_hash)

    await wait_message.edit_text(
        result_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )
    return True


async def inline_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline search: @botname query"""
    
    inline_query = update.inline_query
    query = inline_query.query
    
    if not query or len(query) < 2:
        await inline_query.answer([])
        return
    
    try:
        synthetic_update = Update(update.update_id, inline_query=inline_query)
        if not await ensure_music_access(synthetic_update, context):
            await inline_query.answer([], switch_pm_text="Подпишись на канал для полного доступа", switch_pm_parameter="start")
            return

        # Get Redis service from context
        redis_service = context.bot_data.get("redis_service") or context.bot_data.get("redis")
        downloader = context.bot_data.get("downloader")
        
        if not downloader:
            downloader = MediaDownloader()
        
        # Search cache key
        cache_key = f"inline_search:{query}"
        cached_results = await redis_service.get(cache_key) if redis_service else None
        
        if cached_results:
            results = cached_results
        else:
            # Search YouTube by default for inline
            results = await downloader.search(query, source="youtube", limit=5)
            if redis_service:
                await redis_service.set(cache_key, results, ttl=600)  # 10 min cache
        
        # Convert to InlineQueryResults
        inline_results = []
        for idx, track in enumerate(results):
            result = InlineQueryResultArticle(
                id=f"{idx}_{track.get('id', uuid.uuid4())}",
                title=track.get("title", "Unknown")[:50],
                description=f"Duration: {track.get('duration', 'Unknown')} | {track.get('uploader', 'Unknown')[:30]}",
                input_message_content=InputTextMessageContent(
                    message_text=f"🎵 <b>{track.get('title', 'Unknown')}</b>\n"
                                 f"Duration: {track.get('duration', 'Unknown')}\n"
                                 f"⏱️ Added to queue",
                    parse_mode="HTML"
                ),
                thumb_url=track.get("thumbnail"),
            )
            inline_results.append(result)
        
        await inline_query.answer(inline_results, cache_time=300)
        logger.info(f"Inline search: {query} from @{inline_query.from_user.username}")
        
    except Exception as e:
        logger.error(f"Inline search error: {str(e)}")
        await inline_query.answer([])


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /search command with pagination"""
    
    try:
        if not context.args:
            await update.message.reply_text("❌ Usage: /search <query>")
            return
        
        query = " ".join(context.args)
        user_id = update.effective_user.id
        page = 0
        
        # Send loading message
        wait_msg = await update.message.reply_text(f"🔍 Searching: <b>{query}</b>...", parse_mode="HTML")
        
        sent = await send_search_results(wait_msg, context, query, context.user_data.get("lang", "ru"))
        if sent:
            logger.info(f"Search: {query} by {user_id}")
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def search_pagination_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle pagination buttons: search_next, search_prev"""
    
    query = update.callback_query
    await query.answer()
    
    try:
        # Parse callback: search_next_hash_page or search_prev_hash_page
        parts = query.data.split("_")
        action = parts[1]  # next or prev
        query_hash = parts[2]
        current_page = int(parts[3])
        
        # Get stored results
        results = context.user_data.get(f'search_results_{query_hash}', [])
        
        if not results:
            await query.answer("Results expired, please search again", show_alert=True)
            return
        
        # Calculate new page
        max_pages = (len(results) + 4) // 5  # 5 results per page
        if action == "next":
            new_page = min(current_page + 1, max_pages - 1)
        else:  # prev
            new_page = max(current_page - 1, 0)
        
        # Format text
        text = await _format_search_results(results, new_page, f"Page {new_page + 1}")
        keyboard = await _get_search_keyboard(results, new_page, query_hash)
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")
        logger.info(f"Search pagination: page {new_page}")
        
    except Exception as e:
        logger.error(f"Pagination error: {str(e)}")
        await query.answer(f"Error: {str(e)}", show_alert=True)


async def track_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle track action buttons: listen, download and send audio"""
    
    from app.locales import get_text
    lang = context.user_data.get("lang", "ru")
    
    query = update.callback_query
    await query.answer("🎧")
    
    try:
        callback_data = query.data
        action = callback_data.split("_")[0]
        track_id = "_".join(callback_data.split("_")[1:])
        
        if action == "listen":
            if not await ensure_music_access(update, context):
                return
            url = f"https://youtube.com/watch?v={track_id}"
            
            status_msg = await query.message.reply_text(get_text("downloading", lang), parse_mode="HTML")
            
            dl = context.bot_data.get("downloader")
            if not dl:
                dl = MediaDownloader()
            
            bitrate = context.user_data.get("audio_bitrate", "192")
            result = await dl.download_audio(url, bitrate=bitrate)
            sent = await send_downloaded_audio(query.message, result, lang, status_message=status_msg)
            if sent:
                db = context.bot_data.get("db")
                track = get_track_from_results(context, track_id) or {
                    "id": track_id,
                    "url": url,
                    "title": result.get("title", "Unknown") if result else "Unknown",
                    "source": "youtube",
                    "duration": result.get("duration", 0) if result else 0,
                }
                if db:
                    await db.add_history_entry(update.effective_user.id, track, action="listened")
        
        elif action == "favorite":
            db = context.bot_data.get("db")
            track = get_track_from_results(context, track_id)
            if not db or not track:
                await query.answer("❌ Трек не найден", show_alert=True)
                return

            added = await db.add_to_favorites(update.effective_user.id, track)
            await query.answer("❤️ Добавлено в избранное" if added else "ℹ️ Уже в избранном", show_alert=False)
            logger.info(f"Favorite action for user {update.effective_user.id}: {callback_data}")
        
        else:
            logger.warning(f"Unknown action: {action}")
            await query.answer("Неизвестное действие", show_alert=True)
            
    except Exception as e:
        logger.error(f"Track action error: {str(e)}")
        try:
            await query.message.reply_text(f"❌ Ошибка: {str(e)}")
        except:
            pass


async def _format_search_results(results: list, page: int, title: str) -> str:
    """Format search results for display"""
    
    RESULTS_PER_PAGE = 5
    start_idx = page * RESULTS_PER_PAGE
    end_idx = start_idx + RESULTS_PER_PAGE
    page_results = results[start_idx:end_idx]
    
    text = f"🎵 <b>{title}</b>\n"
    text += f"Page: {page + 1}/{(len(results) + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE}\n\n"
    
    for idx, track in enumerate(page_results, 1):
        result_idx = start_idx + idx
        duration = track.get('duration', 'Unknown')
        title_text = track.get('title', 'Unknown')[:40]
        uploader = track.get('uploader', 'Unknown')[:25]
        
        text += f"<b>{result_idx}. {title_text}</b>\n"
        text += f"   • {uploader}\n"
        text += f"   • ⏱️ {duration}\n\n"
    
    return text


async def _get_search_keyboard(results: list, page: int, query_hash: str) -> list:
    """Generate keyboard for search results"""
    
    RESULTS_PER_PAGE = 5
    max_pages = (len(results) + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE
    start_idx = page * RESULTS_PER_PAGE
    page_results = results[start_idx:start_idx + RESULTS_PER_PAGE]
    
    keyboard = []
    
    # Track action buttons
    for idx, track in enumerate(page_results, 1):
        result_idx = start_idx + idx
        track_id = track.get('id', str(result_idx))
        title = track.get('title', 'Unknown')[:35]
        duration = track.get('duration', 0)
        if isinstance(duration, (int, float)) and duration > 0:
            mins, secs = divmod(int(duration), 60)
            dur_str = f" ({mins}:{secs:02d})"
        else:
            dur_str = ""
        
        keyboard.append([
            InlineKeyboardButton(f"▶️ {result_idx}. {title}{dur_str}", callback_data=f"listen_{track_id}"),
        ])
    
    # Navigation buttons
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"search_prev_{query_hash}_{page}"))
    if page < max_pages - 1:
        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"search_next_{query_hash}_{page}"))
    
    if nav_row:
        keyboard.append(nav_row)
    
    return keyboard
