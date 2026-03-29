"""Helpers for sending downloaded media files and cleaning up temporary files."""

import os
from typing import Optional, Callable, Awaitable, Any
from app.config import Config
from app.locales import get_text
from app.utils.logger import logger


async def _run_tg_call(
    tg_call: Optional[Callable[[Callable[[], Awaitable[Any]]], Awaitable[Any]]],
    coro_factory: Callable[[], Awaitable[Any]],
):
    """Run Telegram API call directly or through a retry wrapper."""
    if tg_call:
        return await tg_call(coro_factory)
    return await coro_factory()


async def send_downloaded_audio(
    reply_target,
    result: dict,
    lang: str,
    status_message=None,
    tg_call: Optional[Callable[[Callable[[], Awaitable[Any]]], Awaitable[Any]]] = None,
) -> bool:
    """Send downloaded audio file and remove temporary files."""
    if not result or not os.path.exists(result.get("path", "")):
        if status_message:
            await _run_tg_call(tg_call, lambda: status_message.edit_text(get_text("download_fail", lang)))
        return False

    file_path = result["path"]
    thumb_path = result.get("thumbnail")
    size_mb = os.path.getsize(file_path) / (1024 * 1024)

    try:
        if size_mb > Config.MAX_FILE_SIZE_MB:
            if status_message:
                await _run_tg_call(tg_call, lambda: status_message.edit_text(get_text("file_too_big", lang)))
            return False

        if status_message:
            await _run_tg_call(tg_call, lambda: status_message.edit_text(get_text("sending", lang), parse_mode="HTML"))

        thumb_file = None
        try:
            if thumb_path and os.path.exists(thumb_path):
                thumb_file = open(thumb_path, "rb")

            with open(file_path, "rb") as audio_file:
                await _run_tg_call(
                    tg_call,
                    lambda: reply_target.reply_audio(
                        audio=audio_file,
                        title=result.get("title", "Unknown"),
                        performer=result.get("artist", "Unknown"),
                        duration=result.get("duration", 0),
                        thumbnail=thumb_file,
                    ),
                )
        finally:
            if thumb_file:
                thumb_file.close()

        if status_message:
            await _run_tg_call(tg_call, lambda: status_message.delete())

        logger.info(
            f"Sent audio: {result.get('title', 'Unknown')} - {result.get('artist', 'Unknown')} ({size_mb:.1f} MB)"
        )
        return True
    finally:
        for path in [file_path, thumb_path]:
            try:
                if path and os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass


async def send_downloaded_video(
    reply_target,
    file_path: str,
    lang: str,
    status_message=None,
    tg_call: Optional[Callable[[Callable[[], Awaitable[Any]]], Awaitable[Any]]] = None,
) -> bool:
    """Send downloaded video file and remove the temporary file."""
    if not file_path or not os.path.exists(file_path):
        if status_message:
            await _run_tg_call(tg_call, lambda: status_message.edit_text(get_text("download_fail", lang)))
        return False

    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    try:
        if size_mb > Config.MAX_FILE_SIZE_MB:
            if status_message:
                await _run_tg_call(tg_call, lambda: status_message.edit_text(get_text("file_too_big", lang)))
            return False

        if status_message:
            await _run_tg_call(tg_call, lambda: status_message.edit_text(get_text("sending", lang), parse_mode="HTML"))

        with open(file_path, "rb") as video_file:
            await _run_tg_call(tg_call, lambda: reply_target.reply_video(video=video_file))

        if status_message:
            await _run_tg_call(tg_call, lambda: status_message.delete())

        logger.info(f"Sent video: {os.path.basename(file_path)} ({size_mb:.1f} MB)")
        return True
    finally:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass