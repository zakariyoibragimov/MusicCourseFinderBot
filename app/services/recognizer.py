"""
Сервис распознавания музыки через Shazam (ShazamAPI + ffmpeg).
Конвертирует аудио через ffmpeg, создаёт fingerprint и отправляет в Shazam.
"""

import os
import subprocess
import tempfile
import asyncio
from app.utils.logger import logger


def _recognize_sync(file_path: str) -> dict | None:
    """Synchronous recognition using ShazamAPI."""
    from ShazamAPI import Shazam
    
    # Convert OGA to WAV via ffmpeg first — ShazamAPI reads via BytesIO/pydub pipe,
    # which fails on OGA format. WAV works reliably through pipe.
    tmp_wav = os.path.join(tempfile.gettempdir(), "shazam_input.wav")
    try:
        result = subprocess.run(
            [
                "ffmpeg", "-y", "-i", file_path,
                "-ar", "44100", "-ac", "1",
                tmp_wav
            ],
            capture_output=True, timeout=15
        )
        
        if result.returncode != 0:
            logger.warning(f"ffmpeg conversion failed: {result.stderr.decode(errors='ignore')[-200:]}")
            return None
        
        if not os.path.exists(tmp_wav) or os.path.getsize(tmp_wav) == 0:
            logger.warning("ffmpeg conversion produced empty file")
            return None
        
        with open(tmp_wav, "rb") as f:
            wav_data = f.read()
        
        shazam = Shazam(wav_data)
        recognize_gen = shazam.recognizeSong()
        
        # Get first recognition result
        offset, result = next(recognize_gen)
        
        tracks = result.get("track")
        if not tracks:
            return None
        
        return {
            "title": tracks.get("title", "Unknown"),
            "artist": tracks.get("subtitle", "Unknown"),
            "album": (
                tracks.get("sections", [{}])[0]
                .get("metadata", [{}])[0]
                .get("text", "")
                if tracks.get("sections")
                and tracks["sections"][0].get("metadata")
                else ""
            ),
            "cover_url": tracks.get("images", {}).get("coverart", ""),
            "shazam_url": tracks.get("url", ""),
            "genre": tracks.get("genres", {}).get("primary", ""),
        }
    finally:
        if os.path.exists(tmp_wav):
            os.remove(tmp_wav)


async def recognize_audio(file_path: str) -> dict | None:
    """
    Распознает музыку из аудиофайла.
    
    Returns:
        dict с ключами title, artist, album, cover_url, shazam_url, genre
        или None если не удалось распознать.
    """
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _recognize_sync, file_path)
    except StopIteration:
        return None
    except Exception as e:
        logger.error(f"Shazam recognition error: {e}")
        return None
