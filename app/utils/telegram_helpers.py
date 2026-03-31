"""Helpers for Telegram-specific edge cases."""

from telegram.error import BadRequest

from app.utils.logger import logger


async def safe_answer_callback(query, *args, **kwargs) -> None:
    """Ignore stale callback answers instead of crashing the handler."""
    try:
        await query.answer(*args, **kwargs)
    except BadRequest as error:
        message = str(error).lower()
        if "query is too old" in message or "query id is invalid" in message:
            logger.warning(f"Skipping stale callback answer: {error}")
            return
        raise