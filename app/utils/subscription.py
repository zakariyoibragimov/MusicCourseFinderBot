"""Helpers for channel subscription checks and free music access limits."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatMemberStatus

from app.config import Config
from app.locales import get_text
from app.utils.logger import logger


ACTIVE_CHAT_MEMBER_STATUSES = {
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.OWNER,
}


def _channel_url() -> str:
    return f"https://t.me/{Config.REQUIRED_CHANNEL_USERNAME.lstrip('@')}"


def get_subscription_markup(lang: str) -> InlineKeyboardMarkup:
    """Build subscription CTA keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text("subscription_join_button", lang), url=_channel_url())],
        [InlineKeyboardButton(get_text("subscription_check_button", lang), callback_data="check_subscription")],
    ])


async def is_user_subscribed(context, user_id: int):
    """Return True if user is subscribed to the required channel, False if not, None on check failure."""
    try:
        member = await context.bot.get_chat_member(Config.REQUIRED_CHANNEL_USERNAME, user_id)
        return member.status in ACTIVE_CHAT_MEMBER_STATUSES
    except Exception as e:
        logger.warning(f"Failed to verify channel subscription for {user_id}: {e}")
        return None


async def get_free_usage_count(context, user) -> int:
    """Get current free music usage count, using DB when available and user_data as fallback."""
    db = context.bot_data.get("db")
    if db:
        try:
            await db.ensure_user(
                user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                language=context.user_data.get("lang", "ru"),
            )
            return await db.get_free_usage_count(user.id)
        except Exception as e:
            logger.warning(f"Failed to load free usage count from DB for {user.id}: {e}")

    return int(context.user_data.get("free_usage_count", 0))


async def increment_free_usage_count(context, user) -> int:
    """Increment free music usage count and return updated value."""
    db = context.bot_data.get("db")
    if db:
        try:
            return await db.increment_free_usage_count(
                user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                language=context.user_data.get("lang", "ru"),
            )
        except Exception as e:
            logger.warning(f"Failed to increment free usage count in DB for {user.id}: {e}")

    updated_value = int(context.user_data.get("free_usage_count", 0)) + 1
    context.user_data["free_usage_count"] = updated_value
    return updated_value


async def send_subscription_required_message(message, lang: str, used_count: int, check_failed: bool = False) -> None:
    """Send or resend the subscription-required message with remaining usage info."""
    remaining = max(0, Config.FREE_MUSIC_REQUEST_LIMIT - used_count)
    key = "subscription_check_failed" if check_failed else "subscription_required"
    text = get_text(
        key,
        lang,
        channel=Config.REQUIRED_CHANNEL_USERNAME,
        limit=Config.FREE_MUSIC_REQUEST_LIMIT,
        remaining=remaining,
    )
    await message.reply_text(text, parse_mode="HTML", reply_markup=get_subscription_markup(lang))


async def ensure_music_access(update: Update, context, consume: bool = True) -> bool:
    """Allow unlimited access for subscribed users and a small free quota for others."""
    user = update.effective_user
    lang = context.user_data.get("lang", "ru")

    subscribed = await is_user_subscribed(context, user.id)
    if subscribed is True:
        return True

    used_count = await get_free_usage_count(context, user)
    if used_count < Config.FREE_MUSIC_REQUEST_LIMIT:
        if consume:
            await increment_free_usage_count(context, user)
        return True

    message = update.callback_query.message if update.callback_query else update.effective_message
    if message is not None:
        await send_subscription_required_message(message, lang, used_count, check_failed=subscribed is None)
    return False