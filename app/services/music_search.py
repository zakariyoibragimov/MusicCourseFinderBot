"""Lightweight music search helpers isolated from yt-dlp imports."""

import json
import os
import subprocess
import sys
from typing import Dict, List, Optional

from ytmusicapi import YTMusic


def _run_clean_python_worker(worker_code: str, args: List[str], timeout: int) -> subprocess.CompletedProcess:
    clean_env = dict(os.environ)
    for key in list(clean_env.keys()):
        if key in {
            "BOT_TOKEN",
            "ADMIN_ID",
            "USE_PROXY",
            "TELEGRAM_USE_ENV_PROXY",
            "TELEGRAM_PROXY_URL",
            "YTMUSIC_PROXY_URL",
            "YTDLP_PROXY_URL",
            "HTTP_PROXY",
            "HTTPS_PROXY",
            "ALL_PROXY",
            "NO_PROXY",
            "http_proxy",
            "https_proxy",
            "all_proxy",
            "no_proxy",
        } or key.startswith("YTDLP_"):
            clean_env.pop(key, None)

    return subprocess.run(
        [sys.executable, "-", *args],
        input=worker_code,
        text=True,
        capture_output=True,
        timeout=timeout,
        env=clean_env,
    )


def _parse_worker_json(stdout: str):
    lines = [line.strip() for line in (stdout or "").splitlines() if line.strip()]
    if not lines:
        return None

    for line in reversed(lines):
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    return None


def _duration_to_seconds(value) -> int:
    if isinstance(value, (int, float)):
        return int(value)
    if not value or not isinstance(value, str):
        return 0

    parts = value.split(":")
    if not all(part.isdigit() for part in parts):
        return 0

    total = 0
    for part in parts:
        total = (total * 60) + int(part)
    return total


def _map_ytmusic_result(entry: Dict) -> Optional[Dict]:
    if not entry:
        return None

    video_id = str(entry.get("videoId") or "")
    if len(video_id) != 11:
        return None

    duration = entry.get("duration_seconds") or _duration_to_seconds(entry.get("duration"))
    if duration > 600:
        return None
    if 0 < duration < 30:
        return None

    artists = entry.get("artists") or []
    artist_names = [artist.get("name") for artist in artists if artist.get("name")]
    thumbnails = entry.get("thumbnails") or []
    thumbnail = thumbnails[-1].get("url") if thumbnails else None

    return {
        "id": video_id,
        "title": entry.get("title", "Unknown"),
        "duration": duration,
        "uploader": ", ".join(artist_names) if artist_names else entry.get("artist", "Unknown"),
        "url": f"https://youtube.com/watch?v={video_id}",
        "thumbnail": thumbnail,
        "source": "youtube",
    }


def search_youtube_music(query: str, limit: int, proxy_url: Optional[str] = None) -> List[Dict]:
    kwargs = {}
    if proxy_url:
        kwargs["proxies"] = {
            "http": proxy_url,
            "https": proxy_url,
        }

    client = YTMusic(**kwargs)
    results: List[Dict] = []
    seen_ids = set()

    for filter_name in ("songs", "videos"):
        entries = client.search(query, filter=filter_name, limit=max(limit * 2, limit))
        for entry in entries:
            track = _map_ytmusic_result(entry)
            if not track:
                continue
            track_id = track["id"]
            if track_id in seen_ids:
                continue

            seen_ids.add(track_id)
            results.append(track)
            if len(results) >= limit:
                return results

    return results


def search_youtube_music_subprocess(query: str, limit: int, proxy_url: Optional[str] = None) -> List[Dict]:
    """Run YouTube Music search in a clean child process to avoid polluted parent env."""
    worker_code = (
        "import json, sys\n"
        "from ytmusicapi import YTMusic\n"
        "query = sys.argv[1]\n"
        "limit = int(sys.argv[2])\n"
        "proxy = sys.argv[3] if len(sys.argv) > 3 else ''\n"
        "kwargs = {}\n"
        "if proxy:\n"
        "    kwargs['proxies'] = {'http': proxy, 'https': proxy}\n"
        "client = YTMusic(**kwargs)\n"
        "def duration_to_seconds(value):\n"
        "    if isinstance(value, (int, float)):\n"
        "        return int(value)\n"
        "    if not value or not isinstance(value, str):\n"
        "        return 0\n"
        "    parts = value.split(':')\n"
        "    if not all(part.isdigit() for part in parts):\n"
        "        return 0\n"
        "    total = 0\n"
        "    for part in parts:\n"
        "        total = (total * 60) + int(part)\n"
        "    return total\n"
        "results = []\n"
        "seen = set()\n"
        "for filter_name in ('songs', 'videos'):\n"
        "    entries = client.search(query, filter=filter_name, limit=max(limit * 2, limit))\n"
        "    for entry in entries:\n"
        "        video_id = str(entry.get('videoId') or '')\n"
        "        if len(video_id) != 11 or video_id in seen:\n"
        "            continue\n"
        "        duration = entry.get('duration_seconds') or duration_to_seconds(entry.get('duration'))\n"
        "        if duration > 600 or (0 < duration < 30):\n"
        "            continue\n"
        "        artists = [artist.get('name') for artist in (entry.get('artists') or []) if artist.get('name')]\n"
        "        thumbnails = entry.get('thumbnails') or []\n"
        "        thumbnail = thumbnails[-1].get('url') if thumbnails else None\n"
        "        results.append({\n"
        "            'id': video_id,\n"
        "            'title': entry.get('title', 'Unknown'),\n"
        "            'duration': duration,\n"
        "            'uploader': ', '.join(artists) if artists else entry.get('artist', 'Unknown'),\n"
        "            'url': f'https://youtube.com/watch?v={video_id}',\n"
        "            'thumbnail': thumbnail,\n"
        "            'source': 'youtube',\n"
        "        })\n"
        "        seen.add(video_id)\n"
        "        if len(results) >= limit:\n"
        "            print(json.dumps(results, ensure_ascii=True))\n"
        "            raise SystemExit(0)\n"
        "print(json.dumps(results, ensure_ascii=True))\n"
    )

    try:
        completed = _run_clean_python_worker(worker_code, [query, str(limit), proxy_url or ""], timeout=20)
    except subprocess.TimeoutExpired:
        return []

    if completed.returncode != 0:
        return []

    payload = _parse_worker_json(completed.stdout)
    if payload is None:
        return []
    return payload if isinstance(payload, list) else []


def download_youtube_audio_subprocess(url: str, output_dir: str, bitrate: str) -> Optional[Dict]:
    worker_code = (
        "import glob, json, os, sys\n"
        "import yt_dlp\n"
        "url = sys.argv[1]\n"
        "output_dir = sys.argv[2]\n"
        "bitrate = sys.argv[3]\n"
        "outtmpl = os.path.join(output_dir, '%(title)s.%(ext)s')\n"
        "opts = {\n"
        "    'quiet': True,\n"
        "    'no_warnings': True,\n"
        "    'noprogress': True,\n"
        "    'socket_timeout': 60,\n"
        "    'noplaylist': True,\n"
        "    'retries': 2,\n"
        "    'extractor_retries': 2,\n"
        "    'geo_bypass': True,\n"
        "    'windowsfilenames': True,\n"
        "    'format': 'bestaudio/best',\n"
        "    'outtmpl': outtmpl,\n"
        "    'postprocessors': [\n"
        "        {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': bitrate},\n"
        "    ],\n"
        "}\n"
        "with yt_dlp.YoutubeDL(opts) as ydl:\n"
        "    info = ydl.extract_info(url, download=True)\n"
        "requested = info.get('requested_downloads') or []\n"
        "mp3_path = requested[-1].get('filepath') if requested else None\n"
        "if not mp3_path or not os.path.exists(mp3_path):\n"
        "    candidates = glob.glob(os.path.join(output_dir, '*.mp3'))\n"
        "    mp3_path = max(candidates, key=os.path.getmtime) if candidates else None\n"
        "thumb_path = None\n"
        "if mp3_path:\n"
        "    base_no_ext = os.path.splitext(mp3_path)[0]\n"
        "    for ext in ('jpg', 'png', 'webp'):\n"
        "        candidate = f'{base_no_ext}.{ext}'\n"
        "        if os.path.exists(candidate):\n"
        "            thumb_path = candidate\n"
        "            break\n"
        "payload = {\n"
        "    'path': mp3_path,\n"
        "    'title': info.get('track') or info.get('title', 'Unknown'),\n"
        "    'artist': info.get('artist') or info.get('uploader', 'Unknown'),\n"
        "    'duration': int(info.get('duration') or 0),\n"
        "    'thumbnail': thumb_path,\n"
        "}\n"
        "print(json.dumps(payload, ensure_ascii=True))\n"
    )

    try:
        completed = _run_clean_python_worker(worker_code, [url, output_dir, bitrate], timeout=180)
    except subprocess.TimeoutExpired:
        return None

    if completed.returncode != 0:
        return None

    payload = _parse_worker_json(completed.stdout)
    if payload is None:
        return None
    return payload if isinstance(payload, dict) and payload.get("path") else None


def download_youtube_video_subprocess(url: str, output_dir: str, resolution: str) -> Optional[str]:
    worker_code = (
        "import glob, json, os, sys\n"
        "import yt_dlp\n"
        "url = sys.argv[1]\n"
        "output_dir = sys.argv[2]\n"
        "resolution = sys.argv[3].replace('p', '')\n"
        "outtmpl = os.path.join(output_dir, '%(title)s.%(ext)s')\n"
        "opts = {\n"
        "    'quiet': True,\n"
        "    'no_warnings': True,\n"
        "    'noprogress': True,\n"
        "    'socket_timeout': 60,\n"
        "    'noplaylist': True,\n"
        "    'retries': 2,\n"
        "    'extractor_retries': 2,\n"
        "    'geo_bypass': True,\n"
        "    'windowsfilenames': True,\n"
        "    'format': f'bestvideo[height<={resolution}]+bestaudio/best[height<={resolution}]',\n"
        "    'outtmpl': outtmpl,\n"
        "    'postprocessors': [\n"
        "        {'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'},\n"
        "    ],\n"
        "}\n"
        "with yt_dlp.YoutubeDL(opts) as ydl:\n"
        "    ydl.extract_info(url, download=True)\n"
        "candidates = []\n"
        "for pattern in ('*.mp4', '*.mkv', '*.webm'):\n"
        "    candidates.extend(glob.glob(os.path.join(output_dir, pattern)))\n"
        "video_path = max(candidates, key=os.path.getmtime) if candidates else None\n"
        "print(json.dumps({'path': video_path}, ensure_ascii=True))\n"
    )

    try:
        completed = _run_clean_python_worker(worker_code, [url, output_dir, resolution], timeout=240)
    except subprocess.TimeoutExpired:
        return None

    if completed.returncode != 0:
        return None

    payload = _parse_worker_json(completed.stdout)
    if payload is None:
        return None
    if not isinstance(payload, dict):
        return None
    return payload.get("path")