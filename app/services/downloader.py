"""
Media downloader service using yt-dlp
Supports YouTube, SoundCloud, Vimeo, TikTok, Instagram, Spotify
"""

import os
import asyncio
from typing import Optional, Callable, Dict, List
from pathlib import Path
import yt_dlp
from yt_dlp.networking.impersonate import ImpersonateTarget
from app.config import Config
from app.services.music_search import (
    download_youtube_audio_subprocess,
    download_youtube_video_subprocess,
    search_youtube_music_subprocess,
)
from app.utils.logger import logger
from app.utils.helpers import get_file_size_mb


class MediaDownloader:
    """Media downloader for various sources"""
    
    def __init__(self):
        """Initialize downloader"""
        Path(Config.DOWNLOADS_DIR).mkdir(parents=True, exist_ok=True)
        self.max_concurrent = Config.MAX_CONCURRENT_DOWNLOADS
        self.semaphore = asyncio.Semaphore(self.max_concurrent)

    @staticmethod
    def _is_downloadable_youtube_entry(entry: Dict) -> bool:
        """Keep only actual video entries and skip channels/playlists."""
        if not entry:
            return False

        entry_id = str(entry.get("id") or "")
        ie_key = str(entry.get("ie_key") or "")
        entry_type = str(entry.get("_type") or "")

        if ie_key and ie_key != "Youtube":
            return False
        if entry_type and entry_type != "url":
            return False
        if len(entry_id) != 11:
            return False
        return True

    @staticmethod
    def _parse_browser_cookies(value: Optional[str]):
        """Parse browser cookies setting for yt-dlp Python API."""
        if not value:
            return None

        browser_spec = value.strip()
        if not browser_spec:
            return None

        browser_part, separator, container = browser_spec.partition("::")
        browser_profile = browser_part.split(":", 1)
        browser_name = browser_profile[0].strip().lower()
        profile = browser_profile[1].strip() if len(browser_profile) > 1 and browser_profile[1].strip() else None
        container_name = container.strip() if separator and container.strip() else None
        return (browser_name, profile, None, container_name)

    def _build_base_ydl_opts(self, *, quiet: bool, no_warnings: bool, download: bool) -> dict:
        """Build common yt-dlp options shared by search and download."""
        ydl_opts = {
            'quiet': quiet,
            'no_warnings': no_warnings,
            'socket_timeout': Config.DOWNLOAD_TIMEOUT,
            'proxy': Config.YTDLP_PROXY_URL,
            'noplaylist': True,
            'retries': 3,
            'extractor_retries': Config.YTDLP_EXTRACTOR_RETRIES,
            'geo_bypass': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            },
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web', 'tv_embedded'],
                }
            },
        }

        if Config.YTDLP_IMPERSONATE:
            try:
                ydl_opts['impersonate'] = ImpersonateTarget.from_str(Config.YTDLP_IMPERSONATE.lower())
            except ValueError as error:
                logger.warning(f"Invalid YTDLP_IMPERSONATE value '{Config.YTDLP_IMPERSONATE}': {error}")

        if Config.YTDLP_COOKIES_FILE and os.path.exists(Config.YTDLP_COOKIES_FILE):
            ydl_opts['cookiefile'] = Config.YTDLP_COOKIES_FILE
        else:
            cookies_from_browser = self._parse_browser_cookies(Config.YTDLP_COOKIES_FROM_BROWSER)
            if cookies_from_browser:
                ydl_opts['cookiesfrombrowser'] = cookies_from_browser

        if not download:
            ydl_opts['skip_download'] = True

        return ydl_opts

    @staticmethod
    def _is_transport_error(error: Exception) -> bool:
        message = str(error).lower()
        markers = [
            "unable to download api page",
            "failed to perform, curl",
            "connection was reset",
            "sslerror",
            "recv failure",
            "timed out",
        ]
        return any(marker in message for marker in markers)

    def _build_search_retry_opts(self, ydl_opts: dict) -> list[dict]:
        """Build conservative retry variants for flaky YouTube search requests."""
        variants = []

        no_proxy = dict(ydl_opts)
        no_proxy.pop('proxy', None)
        variants.append(no_proxy)

        stripped = dict(no_proxy)
        stripped.pop('impersonate', None)
        stripped.pop('cookiefile', None)
        stripped.pop('cookiesfrombrowser', None)
        stripped['extractor_args'] = {
            'youtube': {
                'player_client': ['android'],
            }
        }
        variants.append(stripped)

        plain = dict(stripped)
        plain.pop('http_headers', None)
        variants.append(plain)

        unique_variants = []
        seen = set()
        for variant in variants:
            signature = tuple(sorted((key, repr(value)) for key, value in variant.items()))
            if signature in seen:
                continue
            seen.add(signature)
            unique_variants.append(variant)
        return unique_variants

    @staticmethod
    def _is_bot_check_error(error: Exception) -> bool:
        message = str(error).lower()
        return "sign in to confirm you're not a bot" in message or "cookies-from-browser" in message

    def _browser_cookie_fallbacks(self) -> list[tuple[str, Optional[str], None, Optional[str]]]:
        """Return local browser cookie fallbacks for YouTube downloads."""
        configured = self._parse_browser_cookies(Config.YTDLP_COOKIES_FROM_BROWSER)
        fallbacks = []
        if configured:
            fallbacks.append(configured)

        for browser in ["edge", "chrome", "firefox"]:
            candidate = (browser, None, None, None)
            if candidate not in fallbacks:
                fallbacks.append(candidate)

        return fallbacks

    @staticmethod
    def _is_youtube_url(url: str) -> bool:
        value = (url or "").lower()
        return "youtube.com/" in value or "youtu.be/" in value

    def _prefer_isolated_youtube_download(self, url: str) -> bool:
        """Use the clean worker immediately on Windows where in-process yt-dlp is unstable."""
        return os.name == "nt" and self._is_youtube_url(url)
    
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
                try:
                    music_results = search_youtube_music_subprocess(query, limit, proxy_url=Config.YTMUSIC_PROXY_URL)

                    if music_results:
                        logger.info(f"YTMusic search: {query} - found {len(music_results)} results")
                        return music_results
                except Exception as error:
                    logger.warning(f"YTMusic fallback search error for '{query}': {error}")

                loop = asyncio.get_event_loop()
                ydl_opts = self._build_base_ydl_opts(quiet=True, no_warnings=True, download=False)
                ydl_opts.update({
                    'extract_flat': 'in_playlist',
                })
                attempt_timeout = max(6, min(Config.DOWNLOAD_TIMEOUT, 12))
                search_attempts = [ydl_opts, *self._build_search_retry_opts(ydl_opts)[:1]]

                def _do_search(options):
                    with yt_dlp.YoutubeDL(options) as ydl:
                        return ydl.extract_info(f"ytsearch{limit * 3}:{query}", download=False)

                info = None
                last_error = None

                for attempt, options in enumerate(search_attempts, start=1):
                    try:
                        info = await asyncio.wait_for(
                            loop.run_in_executor(None, lambda opts=options: _do_search(opts)),
                            timeout=attempt_timeout,
                        )
                        if attempt > 1:
                            logger.info(f"YouTube search recovered on retry #{attempt} for query: {query}")
                        break
                    except asyncio.TimeoutError as error:
                        last_error = error
                        logger.warning(f"YouTube search retry #{attempt} timed out for '{query}' after {attempt_timeout}s")
                    except Exception as error:
                        last_error = error
                        if not self._is_transport_error(error):
                            raise
                        logger.warning(f"YouTube search retry #{attempt} failed for '{query}': {error}")

                if info is None and last_error:
                    raise last_error
                
                results = []
                for entry in info.get('entries', []):
                    if not self._is_downloadable_youtube_entry(entry):
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
                ydl_opts = self._build_base_ydl_opts(quiet=True, no_warnings=True, download=False)
                ydl_opts['extract_flat'] = True
                
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
                results = await asyncio.wait_for(
                    loop.run_in_executor(None, _generic_search),
                    timeout=max(10, min(Config.DOWNLOAD_TIMEOUT + 5, 25)),
                )
                
                return results
        
        except asyncio.TimeoutError:
            logger.error(f"Search timeout for query: {query}")
            return []
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
            loop = asyncio.get_event_loop()

            if self._prefer_isolated_youtube_download(url):
                result = await loop.run_in_executor(
                    None,
                    lambda: download_youtube_audio_subprocess(url, Config.DOWNLOADS_DIR, bitrate),
                )
                if result:
                    logger.info(f"Audio download completed via preferred isolated worker: {url}")
                    return result

            output_path = os.path.join(Config.DOWNLOADS_DIR, "%(title)s.%(ext)s")

            base_opts = self._build_base_ydl_opts(quiet=True, no_warnings=True, download=True)
            ydl_opts = {
                'format': '18/best[ext=mp4][acodec!=none]/best[acodec!=none]/bestaudio/best',
                'outtmpl': output_path,
                'writethumbnail': True,
                'windowsfilenames': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android'],
                    }
                },
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
            ydl_opts = {**base_opts, **ydl_opts}
            
            if progress_callback:
                ydl_opts['progress_hooks'] = [self._create_progress_hook(progress_callback)]
            
            info = None
            last_error = None

            try:
                info = await loop.run_in_executor(None, lambda: self._extract_and_download(url, ydl_opts))
            except Exception as error:
                last_error = error
                if self._is_bot_check_error(error):
                    if ydl_opts.get('proxy'):
                        logger.warning(f"Retrying without proxy for {url}: {error}")
                        retry_opts = dict(ydl_opts)
                        retry_opts.pop('proxy', None)
                        try:
                            info = await loop.run_in_executor(None, lambda opts=retry_opts: self._extract_and_download(url, opts))
                            logger.info(f"Audio download succeeded without proxy: {url}")
                        except Exception as retry_error:
                            last_error = retry_error

                    if info is None:
                        logger.warning(f"Retrying with browser cookies for {url}: {last_error}")
                        for cookies_from_browser in self._browser_cookie_fallbacks():
                            retry_opts = dict(ydl_opts)
                            retry_opts.pop('cookiefile', None)
                            retry_opts['cookiesfrombrowser'] = cookies_from_browser
                            try:
                                info = await loop.run_in_executor(None, lambda opts=retry_opts: self._extract_and_download(url, opts))
                                logger.info(f"Audio download succeeded with browser cookies: {cookies_from_browser[0]}")
                                break
                            except Exception as retry_error:
                                last_error = retry_error
                                logger.warning(f"Browser cookie retry failed for {cookies_from_browser[0]}: {retry_error}")
                if info is None and last_error and (
                    self._is_transport_error(last_error) or self._is_bot_check_error(last_error)
                ):
                    logger.warning(f"Falling back to isolated audio download worker for {url}: {last_error}")
                    fallback_result = await loop.run_in_executor(
                        None,
                        lambda: download_youtube_audio_subprocess(url, Config.DOWNLOADS_DIR, bitrate),
                    )
                    if fallback_result:
                        logger.info(f"Audio download succeeded via isolated worker: {url}")
                        return fallback_result
                if info is None and last_error:
                    raise last_error
            
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
            loop = asyncio.get_event_loop()

            if self._prefer_isolated_youtube_download(url):
                video_path = await loop.run_in_executor(
                    None,
                    lambda: download_youtube_video_subprocess(url, Config.DOWNLOADS_DIR, resolution),
                )
                if video_path and os.path.exists(video_path):
                    size_mb = get_file_size_mb(video_path)
                    logger.info(f"Downloaded MP4 via preferred isolated worker: {video_path} ({size_mb:.2f} MB)")
                    return video_path

            output_path = os.path.join(Config.DOWNLOADS_DIR, "%(title)s.%(ext)s")
            res_num = resolution.replace('p', '')

            base_opts = self._build_base_ydl_opts(quiet=False, no_warnings=False, download=True)
            ydl_opts = {
                'format': f'bestvideo[height<={res_num}]+bestaudio/best[height<={res_num}]',
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
                'outtmpl': output_path,
                'windowsfilenames': True,
            }
            ydl_opts = {**base_opts, **ydl_opts}
            
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

            try:
                video_path = await loop.run_in_executor(None, _download_video)
            except Exception as error:
                if self._is_transport_error(error) or self._is_bot_check_error(error):
                    logger.warning(f"Falling back to isolated video download worker for {url}: {error}")
                    video_path = await loop.run_in_executor(
                        None,
                        lambda: download_youtube_video_subprocess(url, Config.DOWNLOADS_DIR, resolution),
                    )
                else:
                    raise
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
