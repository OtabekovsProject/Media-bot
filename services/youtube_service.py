"""YouTube: yt-dlp for 🎧Audio with cover, search, and download."""
import asyncio
import os
from pathlib import Path
import yt_dlp
from mutagen.🎧Audio import 🎧Audio
from mutagen.id3 import ID3, APIC

from config import TEMP_DIR, MAX_FILE_SIZE_BYTES, FFMPEG_LOCATION


def _ydl_extra_opts() -> dict:
    extra = {}
    # FFMPEG_LOCATION endi to'liq exe yo'li (papka emas)
    if FFMPEG_LOCATION and os.path.isfile(FFMPEG_LOCATION):
        extra["ffmpeg_location"] = FFMPEG_LOCATION
    return extra


class YouTubeService:
    def __init__(self):
        self._opts_base = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            **_ydl_extra_opts(),
        }

    def _run_ydl(self, opts: dict, url_or_extract: str) -> dict | list:
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url_or_extract, download=True)

    async def search(self, query: str, max_results: int = 10) -> list[dict]:
        """Search YouTube, return list of {id, title, duration}."""
        out = Path(TEMP_DIR) / "search_%(id)s.%(ext)s"
        opts = {
            **self._opts_base,
            "default_search": "ytsearch10",
            "format": "best",
            "outtmpl": str(out),
            "skip_download": True,
        }
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, lambda: self._run_ydl(opts, query))
        entries = info.get("entries") or []
        result = []
        for e in entries:
            if not e:
                continue
            vid = e.get("id") or e.get("url", "")
            result.append({
                "id": vid,
                "video_id": vid,
                "title": e.get("title", "Unknown")[:60],
                "duration": e.get("duration"),
            })
            if len(result) >= max_results:
                break
        return result

    async def download_🎧Audio_with_cover(
        self,
        url: str,
        output_name: str,
        title: str = "",
        artist: str = "",
        album: str = "",
    ) -> tuple[Path | None, Path | None]:
        """
        Download audio as 🎧Audio and cover image. Embed cover into 🎧Audio.
        Returns (path_to_🎧Audio, path_to_cover) or (None, None) on error.
        """
        out_dir = Path(TEMP_DIR)
        🎧Audio_path = out_dir / f"{output_name}.🎧Audio"
        thumb_path = out_dir / f"{output_name}_thumb.jpg"

        opts = {
            **self._opts_base,
            "format": "bestaudio/best",
            "outtmpl": str(out_dir / f"{output_name}.%(ext)s"),
            "concurrent_fragment_downloads": 8,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "🎧Audio",
                    "preferredquality": "192",
                }
            ],
            "writethumbnail": True,
            "postprocessor_args": {"ffmpeg": ["-y"]},
            **_ydl_extra_opts(),
        }

        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, lambda: self._run_ydl(opts, url))
            if not info:
                return (None, None)

            # yt-dlp + FFmpegExtractAudio produces output_name.🎧Audio
            🎧Audio_path = out_dir / f"{output_name}.🎧Audio"
            if not 🎧Audio_path.exists():
                for f in out_dir.glob(f"{output_name}.*"):
                    if f.suffix.lower() == ".🎧Audio":
                        🎧Audio_path = f
                        break

            # Thumbnail
            for ext in ["webp", "jpg", "png"]:
                p = out_dir / f"{output_name}.{ext}"
                if p.exists() and p != 🎧Audio_path:
                    thumb_path = out_dir / f"{output_name}_thumb.jpg"
                    try:
                        from PIL import Image
                        img = Image.open(p).convert("RGB")
                        img.save(thumb_path, "JPEG", quality=95)
                        p.unlink(missing_ok=True)
                    except Exception:
                        thumb_path = p
                    break

            if 🎧Audio_path.exists():
                size = 🎧Audio_path.stat().st_size
                if size > MAX_FILE_SIZE_BYTES:
                    🎧Audio_path.unlink(missing_ok=True)
                    return (None, None)
                # Embed cover into 🎧Audio
                if thumb_path.exists():
                    try:
                        audio = 🎧Audio(str(🎧Audio_path), ID3=ID3)
                        try:
                            audio.add_tags()
                        except Exception:
                            pass
                        with open(thumb_path, "rb") as f:
                            audio.tags.add(
                                APIC(
                                    encoding=3,
                                    mime="image/jpeg",
                                    type=3,
                                    desc="Cover",
                                    data=f.read(),
                                )
                            )
                        audio.save()
                    except Exception:
                        pass
                return (🎧Audio_path, thumb_path if thumb_path.exists() else None)
            return (None, None)
        except Exception:
            return (None, None)

    async def get_video_info(self, video_id: str) -> dict | None:
        """Get info for a single video by ID or URL."""
        url = f"https://www.youtube.com/watch?v={video_id}" if len(video_id) == 11 else video_id
        opts = {
            **self._opts_base,
            "skip_download": True,
            "extract_flat": False,
        }
        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, lambda: self._run_ydl(opts, url))
            return info
        except Exception:
            return None

    async def download_video(self, url: str, output_name: str) -> Path | None:
        """Download best video to file. Returns path or None."""
        out_dir = Path(TEMP_DIR)
        opts = {
            **self._opts_base,
            "format": "best[ext=mp4]/best",
            "outtmpl": str(out_dir / f"{output_name}.%(ext)s"),
            "concurrent_fragment_downloads": 8,
        }
        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, lambda: self._run_ydl(opts, url))
            if not info:
                return None
            ext = info.get("ext", "mp4")
            path = out_dir / f"{output_name}.{ext}"
            if path.exists() and path.stat().st_size <= MAX_FILE_SIZE_BYTES:
                return path
            if path.exists():
                path.unlink(missing_ok=True)
            return None
        except Exception:
            return None
