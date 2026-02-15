"""Detect platform and download media (Instagram, YouTube, TikTok, Pinterest)."""
import asyncio
import subprocess
from pathlib import Path
from typing import Optional

from config import TEMP_DIR, MAX_FILE_SIZE_BYTES


def _run_yt_dlp(args: list[str], cwd: Optional[Path] = None) -> tuple[bool, str]:
    try:
        r = subprocess.run(
            ["yt-dlp", "--no-warnings", "-q", *args],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=cwd or TEMP_DIR,
        )
        return r.returncode == 0, (r.stderr or r.stdout or "")
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        return False, str(e)


def _detect_platform(url: str) -> str:
    url_lower = url.lower().strip()
    if "instagram.com" in url_lower or "instagr.am" in url_lower:
        return "instagram"
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "youtube"
    if "tiktok.com" in url_lower or "vm.tiktok" in url_lower:
        return "tiktok"
    if "pinterest" in url_lower or "pin.it" in url_lower:
        return "pinterest"
    return "unknown"


def detect_platform(url: str) -> str:
    """Return: instagram | youtube | tiktok | pinterest | unknown."""
    return _detect_platform(url)


async def download_media(
    url: str,
    user_id: int,
    want_video: bool = True,
) -> tuple[Optional[Path], str]:
    """
    Download media from URL. want_video: for YouTube we can choose video or audio.
    Returns (path_to_file, mime_type) or (None, '').
    For TikTok we try to get without watermark.
    """
    platform = _detect_platform(url)
    out_dir = TEMP_DIR / str(user_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_tpl = str(out_dir / "media.%(ext)s")
    loop = asyncio.get_event_loop()

    if platform == "youtube":
        if want_video:
            ok, _ = await loop.run_in_executor(
                None,
                lambda: _run_yt_dlp([
                    "-f", "best[ext=mp4]/best",
                    "-o", out_tpl,
                    "--no-playlist",
                    url,
                ], cwd=out_dir),
            )
        else:
            ok, _ = await loop.run_in_executor(
                None,
                lambda: _run_yt_dlp([
                    "-x", "--audio-format", "🎧Audio",
                    "-o", out_tpl,
                    "--no-playlist",
                    url,
                ], cwd=out_dir),
            )
    elif platform == "tiktok":
        # Prefer no watermark
        ok, _ = await loop.run_in_executor(
            None,
            lambda: _run_yt_dlp([
                "-f", "best[ext=mp4]/best",
                "-o", out_tpl,
                "--no-playlist",
                url,
            ], cwd=out_dir),
        )
    elif platform in ("instagram", "pinterest"):
        ok, _ = await loop.run_in_executor(
            None,
            lambda: _run_yt_dlp([
                "-f", "best",
                "-o", out_tpl,
                "--no-playlist",
                url,
            ], cwd=out_dir),
        )
    else:
        return None, ""

    if not ok:
        return None, ""

    # Find downloaded file
    for f in out_dir.glob("media.*"):
        if f.is_file() and f.stat().st_size <= MAX_FILE_SIZE_BYTES:
            ext = f.suffix.lower()
            mime = "video/mp4" if ext in (".mp4", ".webm", ".mkv") else "image/jpeg"
            if ext == ".png":
                mime = "image/png"
            elif ext == ".🎧Audio":
                mime = "audio/mpeg"
            return f, mime
    return None, ""
