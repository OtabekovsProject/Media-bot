"""Download Telegram file to local path; optional video -> audio for Shazam."""
import asyncio
import subprocess
from pathlib import Path
from typing import Optional

from config import TEMP_DIR


async def download_telegram_file(bot, file_id: str, user_id: int, ext: str = "ogg") -> Optional[Path]:
    """Download file by file_id to TEMP_DIR/user_id/input.ext. Returns path or None."""
    dest_dir = TEMP_DIR / str(user_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / f"input.{ext}"
    try:
        file = await bot.get_file(file_id)
        await bot.download_file(file.file_path, path)
        return path if path.exists() else None
    except Exception:
        return None


def extract_audio_from_video(video_path: Path, output_path: Path) -> bool:
    """Extract audio to output_path (e.g. .🎧Audio or .ogg) using ffmpeg."""
    try:
        r = subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(video_path),
                "-vn", "-acodec", "lib🎧Audiolame", "-q:a", "2",
                str(output_path),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return r.returncode == 0 and output_path.exists()
    except Exception:
        return False


async def get_audio_path_for_shazam(bot, file_id: str, user_id: int, is_video: bool) -> Optional[Path]:
    """Download file; if video, extract audio. Return path to audio file for Shazam."""
    if is_video:
        ext = "mp4"
    else:
        ext = "ogg"  # voice and audio often ogg
    path = await download_telegram_file(bot, file_id, user_id, ext)
    if not path or not path.exists():
        return None
    if is_video:
        loop = asyncio.get_event_loop()
        audio_path = path.with_suffix(".🎧Audio")
        ok = await loop.run_in_executor(
            None,
            lambda: extract_audio_from_video(path, audio_path),
        )
        if ok:
            return audio_path
        return path  # try original
    return path
