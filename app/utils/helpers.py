"""
Helper functions for the bot
"""

import os
import re
from typing import List, Tuple, Optional
from pathlib import Path
from datetime import datetime, timedelta
from app.utils.logger import logger


def format_duration(seconds: int) -> str:
    """Format seconds to HH:MM:SS."""
    try:
        total_seconds = max(0, int(seconds or 0))
    except (TypeError, ValueError):
        return "--:--"

    if total_seconds == 0:
        return "00:00"

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def extract_urls(text: str) -> List[str]:
    """Extract URLs from text"""
    url_pattern = r'https?://[^\s]+'
    return re.findall(url_pattern, text)


def is_valid_url(url: str) -> bool:
    """Check if string is valid URL"""
    url_pattern = r'^https?://'
    return bool(re.match(url_pattern, url))


def get_source_from_url(url: str) -> Optional[str]:
    """Detect media source from URL"""
    sources = {
        'youtube': ['youtube.com', 'youtu.be'],
        'soundcloud': ['soundcloud.com'],
        'vimeo': ['vimeo.com'],
        'tiktok': ['tiktok.com', 'vm.tiktok.com'],
        'instagram': ['instagram.com'],
        'spotify': ['spotify.com'],
    }
    
    url_lower = url.lower()
    for source, patterns in sources.items():
        if any(pattern in url_lower for pattern in patterns):
            return source
    
    return None


def get_file_size_mb(file_path: str) -> float:
    """Get file size in MB"""
    if not os.path.exists(file_path):
        return 0
    return os.path.getsize(file_path) / (1024 * 1024)


def get_cache_size_gb() -> float:
    """Get total cache directory size in GB"""
    from app.config import Config
    
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(Config.CACHE_DIR):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if os.path.exists(filepath):
                total_size += os.path.getsize(filepath)
    
    return total_size / (1024 * 1024 * 1024)


def clean_cache(max_age_days: int = 7, max_size_gb: int = 10) -> Tuple[int, float]:
    """
    Clean cache directory
    
    Args:
        max_age_days: Delete files older than this
        max_size_gb: If cache exceeds this, delete oldest files
    
    Returns:
        (deleted_count, freed_size_mb)
    """
    from app.config import Config
    
    deleted_count = 0
    freed_size = 0
    now = datetime.now()
    cutoff_date = now - timedelta(days=max_age_days)
    
    files_with_dates = []
    
    # Collect all files with modification times
    for dirpath, dirnames, filenames in os.walk(Config.CACHE_DIR):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                size = os.path.getsize(filepath)
                files_with_dates.append((filepath, mtime, size))
            except OSError:
                continue
    
    # Delete old files
    for filepath, mtime, size in files_with_dates:
        if mtime < cutoff_date:
            try:
                os.remove(filepath)
                deleted_count += 1
                freed_size += size
            except OSError as e:
                logger.warning(f"Error deleting cache file {filepath}: {e}")
    
    # If still over size limit, delete oldest files
    cache_size_gb = get_cache_size_gb()
    if cache_size_gb > max_size_gb:
        # Sort by modification time (oldest first)
        files_with_dates.sort(key=lambda x: x[1])
        target_size = max_size_gb * 1024 * 1024 * 1024 * 0.9  # 90% of limit
        current_size = cache_size_gb * 1024 * 1024 * 1024
        
        for filepath, _, size in files_with_dates:
            if current_size <= target_size:
                break
            
            try:
                os.remove(filepath)
                deleted_count += 1
                freed_size += size
                current_size -= size
            except OSError as e:
                logger.warning(f"Error deleting cache file {filepath}: {e}")
    
    return deleted_count, freed_size / (1024 * 1024)  # Return MB


def escape_markdown(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2"""
    special_chars = r'_[]()~`>#+-=|{}.!\\'
    result = ""
    for char in text:
        if char in special_chars:
            result += "\\" + char
        else:
            result += char
    return result


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to max length with ellipsis"""
    if len(text) > max_length:
        return text[:max_length-3] + "..."
    return text
