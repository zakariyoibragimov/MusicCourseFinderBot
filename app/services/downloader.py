"""
Media downloader service using yt-dlp
Supports YouTube, SoundCloud, Vimeo, TikTok, Instagram, Spotify
"""

import os
import asyncio
from typing import Optional, Callable, Dict, List
from pathlib import Path
import yt_dlp
from app.config import Config
from app.utils.logger import logger
from app.utils.helpers import get_file_size_mb


class MediaDownloader:
    """Media downloader for various sources"""
    
    def __init__(self):
        """Initialize downloader"""
        Path(Config.DOWNLOADS_DIR).mkdir(parents=True, exist_ok=True)
        self.max_concurrent = Config.MAX_CONCURRENT_DOWNLOADS
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
    
    async def search(
        self,
        query: str,
        source: str = "youtube",
        limit: int = 5
    ) -> List[Dict]:
        """
        Search for media
        
        Args:
            query: Search query
            source: Media source (youtube, soundcloud, etc)
            limit: Number of results
        
        Returns:
            List of search results
        """
        try:
            if source == "youtube":
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': 'in_playlist',
                    'skip_download': True,
                    'socket_timeout': 10,
                }
                
                def _do_search():
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        return ydl.extract_info(f"ytsearch{limit * 3}:{query}", download=False)
                
                loop = asyncio.get_event_loop()
                info = await loop.run_in_executor(None, _do_search)
                
                results = []
                for entry in info.get('entries', []):
                    if entry is None:
                        continue
                    
                    duration = entry.get('duration') or 0
                    # Пропускаем треки длиннее 10 минут (если длительность известна)
                    if duration > 600:
                        continue
                    # Пропускаем слишком короткие (превью, фрагменты)
                    if 0 < duration < 30:
                        continue
                    
                    results.append({
                        'id': entry.get('id'),
                        'title': entry.get('title', 'Unknown'),
                        'duration': duration,
                        'uploader': entry.get('uploader', 'Unknown'),
                        'url': f"https://youtube.com/watch?v={entry.get('id')}",
                        'thumbnail': entry.get('thumbnail'),
                        'source': 'youtube',
                    })
                    
                    if len(results) >= limit:
                        break
                
                logger.info(f"YouTube search: {query} - found {len(results)} results")
                return results
            
            elif source == "soundcloud":
                # SoundCloud search (requires API key if available)
                logger.info(f"SoundCloud search: {query}")
                # TODO: Implement SoundCloud search
                return []
            
            else:
                # Try generic yt-dlp search
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': True,
                    'skip_download': True,
                    'socket_timeout': 10,
                }
                
                def _generic_search():
                    results = []
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        try:
                            info = ydl.extract_info(query, download=False)
                            if 'entries' in info:
                                for entry in info['entries'][:limit]:
                                    if entry:
                                        results.append({
                                            'id': entry.get('id'),
                                            'title': entry.get('title', 'Unknown'),
                                            'duration': entry.get('duration', 0),
                                            'uploader': entry.get('uploader', 'Unknown'),
                                            'url': entry.get('url'),
                                            'source': source,
                                        })
                        except Exception:
                            return []
                    return results

                loop = asyncio.get_event_loop()
                results = await loop.run_in_executor(None, _generic_search)
                
                return results
        
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    async def download_audio(
        self,
        url: str,
        bitrate: str = "192",
        progress_callback: Optional[Callable] = None
    ) -> Optional[str]:
        """
        Download audio as MP3
        
        Args:
            url: Media URL
            bitrate: Audio bitrate (96, 128, 192, 320)
            progress_callback: Progress callback function
        
        Returns:
            Path to downloaded file or None
        """
        async with self.semaphore:
            return await self._download_audio_impl(url, bitrate, progress_callback)
    
    async def _download_audio_impl(
        self,
        url: str,
        bitrate: str,
        progress_callback: Optional[Callable]
    ) -> Optional[Dict]:
        """Internal implementation. Returns dict with path and metadata."""
        try:
            output_path = os.path.join(Config.DOWNLOADS_DIR, "%(title)s.%(ext)s")
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': bitrate,
                }],
                'outtmpl': output_path,
                'quiet': True,
                'no_warnings': True,
                'socket_timeout': Config.DOWNLOAD_TIMEOUT,
                'http_headers': {'User-Agent': 'Mozilla/5.0'},
                'writethumbnail': True,
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': bitrate,
                    },
                    {
                        'key': 'FFmpegThumbnailsConvertor',
                        'format': 'jpg',
                    },
                ],
            }
            
            if progress_callback:
                ydl_opts['progress_hooks'] = [self._create_progress_hook(progress_callback)]
            
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, lambda: self._extract_and_download(url, ydl_opts))
            
            if not info:
                return None
            
            # Find the actual downloaded mp3 file via requested_downloads or glob
            mp3_path = None
            requested = info.get('requested_downloads', [])
            if requested:
                mp3_path = requested[-1].get('filepath')
            
            if not mp3_path or not os.path.exists(mp3_path):
                # Fallback: use yt-dlp sanitized filename
                import yt_dlp.utils
                sanitized_title = yt_dlp.utils.sanitize_filename(info.get('title', 'audio'))
                mp3_path = os.path.join(Config.DOWNLOADS_DIR, f"{sanitized_title}.mp3")
            
            if not mp3_path or not os.path.exists(mp3_path):
                # Last fallback: find most recent mp3 in downloads dir
                import glob
                mp3_files = glob.glob(os.path.join(Config.DOWNLOADS_DIR, "*.mp3"))
                if mp3_files:
                    mp3_path = max(mp3_files, key=os.path.getmtime)
            
            if mp3_path and os.path.exists(mp3_path):
                size_mb = get_file_size_mb(mp3_path)
                logger.info(f"Downloaded MP3: {mp3_path} ({size_mb:.2f} MB)")
                
                # Find thumbnail near the mp3 file
                thumb_path = None
                base_no_ext = os.path.splitext(mp3_path)[0]
                for ext in ['jpg', 'png', 'webp']:
                    test_thumb = f"{base_no_ext}.{ext}"
                    if os.path.exists(test_thumb):
                        thumb_path = test_thumb
                        break
                
                return {
                    'path': mp3_path,
                    'title': info.get('track') or info.get('title', 'Unknown'),
                    'artist': info.get('artist') or info.get('uploader', 'Unknown'),
                    'duration': int(info.get('duration', 0)),
                    'thumbnail': thumb_path,
                }
            
            logger.error(f"MP3 file not found after download for: {info.get('title')}")
                    
        except Exception as e:
            logger.error(f"Audio download error: {e}")
        
        return None
    
    def _extract_and_download(self, url: str, ydl_opts: dict):
        """Sync download wrapper for run_in_executor"""
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=True)
    
    async def download_video(
        self,
        url: str,
        resolution: str = "720",
        progress_callback: Optional[Callable] = None
    ) -> Optional[str]:
        """
        Download video as MP4
        
        Args:
            url: Media URL
            resolution: Video resolution (480p, 720p, 1080p)
            progress_callback: Progress callback function
        
        Returns:
            Path to downloaded file or None
        """
        async with self.semaphore:
            return await self._download_video_impl(url, resolution, progress_callback)
    
    async def _download_video_impl(
        self,
        url: str,
        resolution: str,
        progress_callback: Optional[Callable]
    ) -> Optional[str]:
        """Internal implementation"""
        try:
            output_path = os.path.join(Config.DOWNLOADS_DIR, "%(title)s.%(ext)s")
            res_num = resolution.replace('p', '')
            
            ydl_opts = {
                'format': f'bestvideo[height<={res_num}]+bestaudio/best[height<={res_num}]',
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
                'outtmpl': output_path,
                'quiet': False,
                'no_warnings': False,
                'socket_timeout': Config.DOWNLOAD_TIMEOUT,
                'http_headers': {'User-Agent': 'Mozilla/5.0'}
            }
            
            if progress_callback:
                ydl_opts['progress_hooks'] = [self._create_progress_hook(progress_callback)]
            
            def _download_video():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    for ext in ['mp4', 'mkv', 'webm']:
                        test_path = output_path.replace('%(ext)s', ext) % {'title': info.get('title', 'video')}
                        if os.path.exists(test_path):
                            return test_path
                return None

            loop = asyncio.get_event_loop()
            video_path = await loop.run_in_executor(None, _download_video)
            if video_path and os.path.exists(video_path):
                size_mb = get_file_size_mb(video_path)
                logger.info(f"Downloaded MP4: {video_path} ({size_mb:.2f} MB)")
                return video_path
                        
        except Exception as e:
            logger.error(f"Video download error: {e}")
        
        return None
    
    def _create_progress_hook(self, callback: Callable):
        """Create progress hook for yt-dlp"""
        def progress_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                
                if total:
                    percent = int((downloaded / total) * 100)
                    speed = d.get('speed', 0)
                    eta = d.get('eta', 0)
                    # Schedule callback as coroutine if it's async
                    try:
                        asyncio.create_task(callback(percent, speed, eta) if asyncio.iscoroutine(callback(percent, speed, eta)) else callback(percent, speed, eta))
                    except:
                        callback(percent, speed, eta)
        
        return progress_hook
    
    async def get_playlist_tracks(self, url: str) -> List[Dict]:
        """Get all tracks from playlist"""
        try:
            ydl_opts = {
                'extract_flat': True,
                'skip_download': True,
                'quiet': True,
                'no_warnings': True,
            }
            
            def _playlist_tracks():
                tracks = []
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if 'entries' in info:
                        for entry in info['entries']:
                            if entry:
                                tracks.append({
                                    'id': entry.get('id'),
                                    'title': entry.get('title', 'Unknown'),
                                    'duration': entry.get('duration', 0),
                                    'url': entry.get('url'),
                                })
                return tracks

            loop = asyncio.get_event_loop()
            tracks = await loop.run_in_executor(None, _playlist_tracks)
            
            logger.info(f"Playlist: {url} - found {len(tracks)} tracks")
            return tracks
        
        except Exception as e:
            logger.error(f"Playlist error: {e}")
            return []


# Global instance
downloader = MediaDownloader()
