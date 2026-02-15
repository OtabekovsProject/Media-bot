"""Media download from Instagram, TikTok, Pinterest, Facebook, YouTube (video)."""
import asyncio
import re
from pathlib import Path
import yt_dlp

from config import TEMP_DIR, MAX_FILE_SIZE_BYTES, FFMPEG_LOCATION

# URL patterns
YT_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.|m\.)?(?:youtube\.com/(?:watch\?v=|shorts/|embed/)|youtu\.be/)([a-zA-Z0-9_-]{11})"
)
INSTA_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?instagram\.com/(?:p|reel|reels)/([a-zA-Z0-9_-]+)"
)
TIKTOK_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?(?:tiktok\.com|vm\.tiktok\.com)/[^\s]+"
)
PINTEREST_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?pinterest\.(?:com|ru)/[^\s]+"
)
FACEBOOK_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.|m\.)?(?:facebook\.com|fb\.watch|fb\.com|fb.watch)/[^\s]+"
)


def _ydl_opts(prefix: str, format_best: bool = False, audio_only: bool = False, platform: str | None = None) -> dict:
    out = Path(TEMP_DIR) / f"{prefix}_%(id)s.%(ext)s"
    opts = {
        "quiet": True,
        "no_warnings": True,
        "outtmpl": str(out),
        "format": "best" if format_best else "best[ext=mp4]/best/bestvideo+bestaudio",
        "socket_timeout": 45,
        "retries": 5,
        "fragment_retries": 3,
    }
    if audio_only:
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [
            {"key": "FFmpegExtractAudio", "preferredcodec": "🎧Audio", "preferredquality": "192"}
        ]
        opts["postprocessor_args"] = {"ffmpeg": ["-y"]}
    if FFMPEG_LOCATION:
        opts["ffmpeg_location"] = FFMPEG_LOCATION
    # Platformaga qarab qo'shimcha – Instagram/TikTok/Facebook to'liq video va audio
    if platform == "Instagram":
        opts.setdefault("extractor_args", {})["instagram"] = {"format": "best"}
    elif platform == "TikTok":
        opts.setdefault("extractor_args", {})["tiktok"] = {"format": "best"}
    elif platform == "Facebook":
        opts.setdefault("extractor_args", {})["facebook"] = {"format": "best"}
    return opts


class MediaDownloaderService:
    @staticmethod
    def detect_platform(url: str) -> str | None:
        if YT_PATTERN.search(url):
            return "YouTube"
        if INSTA_PATTERN.search(url):
            return "Instagram"
        if TIKTOK_PATTERN.search(url):
            return "TikTok"
        if PINTEREST_PATTERN.search(url):
            return "Pinterest"
        if FACEBOOK_PATTERN.search(url):
            return "Facebook"
        return None

    def _run_ydl(self, opts: dict, url: str):
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=True)

    async def _download_generic(self, url: str, prefix: str, retries: int = 2) -> Path | None:
        """Video yuklash: Instagram/TikTok/Facebook/Pinterest – to'liq va aniq."""
        platform = self.detect_platform(url)
        loop = asyncio.get_event_loop()
        for attempt in range(max(1, retries)):
            try:
                opts = _ydl_opts(prefix, format_best=True, platform=platform)
                info = await loop.run_in_executor(
                    None, lambda u=url, o=opts: self._run_ydl(o, u)
                )
                if not info:
                    continue
                requested = info.get("requested_downloads") or []
                for d in requested:
                    p = Path(d.get("filepath", d.get("filename", "")))
                    if p.exists() and p.stat().st_size <= MAX_FILE_SIZE_BYTES:
                        return p
                for f in TEMP_DIR.iterdir():
                    if f.is_file() and f.name.startswith(prefix) and f.stat().st_size <= MAX_FILE_SIZE_BYTES:
                        return f
            except Exception:
                if attempt == retries - 1:
                    return None
        return None

    async def download_instagram(self, url: str, prefix: str) -> Path | None:
        return await self._download_generic(url, prefix)

    async def download_tiktok(self, url: str, prefix: str) -> Path | None:
        return await self._download_generic(url, prefix)

    async def download_pinterest(self, url: str, prefix: str) -> Path | None:
        return await self._download_generic(url, prefix)

    async def download_facebook(self, url: str, prefix: str) -> Path | None:
        return await self._download_generic(url, prefix)

    async def download_video_or_image(self, url: str, prefix: str) -> Path | None:
        """Istalgan platforma (Instagram/TikTok/Facebook/Pinterest) uchun video."""
        return await self._download_generic(url, prefix)

    async def download_as_🎧Audio(self, url: str, prefix: str, retries: int = 2) -> Path | None:
        """Havoladan 🎧Audio – videodan musiqani ajratib (Instagram/TikTok/Facebook va b.)."""
        platform = self.detect_platform(url)
        loop = asyncio.get_event_loop()
        opts = _ydl_opts(prefix, format_best=False, audio_only=True, platform=platform)
        opts["outtmpl"] = str(TEMP_DIR / f"{prefix}.%(ext)s")
        for attempt in range(max(1, retries)):
            try:
                info = await loop.run_in_executor(None, lambda u=url, o=opts: self._run_ydl(o, u))
                if not info:
                    continue
                🎧Audio_path = TEMP_DIR / f"{prefix}.🎧Audio"
                if 🎧Audio_path.exists() and 🎧Audio_path.stat().st_size <= MAX_FILE_SIZE_BYTES:
                    return 🎧Audio_path
                for f in TEMP_DIR.iterdir():
                    if f.is_file() and f.name.startswith(prefix) and f.suffix.lower() == ".🎧Audio":
                        if f.stat().st_size <= MAX_FILE_SIZE_BYTES:
                            return f
            except Exception:
                if attempt == retries - 1:
                    return None
        return None

    async def download_youtube_video(self, url: str, prefix: str) -> Path | None:
        """Download YouTube as video (mp4)."""
        opts = _ydl_opts(prefix)
        opts["outtmpl"] = str(TEMP_DIR / f"{prefix}.%(ext)s")
        opts["format"] = "best[ext=mp4]/best"
        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, lambda: self._run_ydl(opts, url))
            if not info:
                return None
            ext = info.get("ext", "mp4")
            path = TEMP_DIR / f"{prefix}.{ext}"
            if path.exists() and path.stat().st_size <= MAX_FILE_SIZE_BYTES:
                return path
            if path.exists():
                path.unlink(missing_ok=True)
            return None
        except Exception:
            return None
