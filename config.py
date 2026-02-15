"""Bot configuration from environment."""
import os
import shutil
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
# Port: 0 = o'chirilgan. 8080 yoki boshqa – bot uxlamasligi uchun health server (Railway, Render va b.)
PORT = int(os.getenv("PORT", "0"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)


def _find_ffmpeg_exe() -> str | None:
    """FFmpeg executable to'liq yo'lini topish (papka yoki exe)."""
    env_path = os.getenv("FFMPEG_LOCATION", "").strip()
    if env_path:
        p = Path(env_path)
        if p.is_file():
            return str(p.resolve())
        if (p / "ffmpeg.exe").exists():
            return str((p / "ffmpeg.exe").resolve())
    # PATH da bormi?
    ffmpeg_exe = shutil.which("ffmpeg")
    if ffmpeg_exe:
        return str(Path(ffmpeg_exe).resolve())
    # Windows: odatiy joylar
    user_home = os.environ.get("USERPROFILE", os.environ.get("HOME", ""))
    candidates = [
        Path("C:/ffmpeg/bin"),
        Path("C:/ffmpeg"),
        Path(user_home) / "ffmpeg" / "bin" if user_home else None,
        Path(os.environ.get("LOCALAPPDATA", "")) / "ffmpeg" / "bin",
        Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "ffmpeg" / "bin",
    ]
    for p in candidates:
        if p is None:
            continue
        p = Path(p)
        if (p / "ffmpeg.exe").exists():
            return str((p / "ffmpeg.exe").resolve())
        for sub in p.iterdir() if p.exists() else []:
            if sub.is_dir() and (sub / "ffmpeg.exe").exists():
                return str((sub / "ffmpeg.exe").resolve())
    # imageio-ffmpeg: exe boshqa nomda (ffmpeg-win64-...) bo'ladi
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.isfile(exe):
            return str(Path(exe).resolve())
    except Exception:
        pass
    return None


# FFmpeg executable to'liq yo'li (yt-dlp va tekshiruv uchun)
FFMPEG_LOCATION = _find_ffmpeg_exe()


def _find_ffprobe_exe() -> str | None:
    """FFprobe exe yo'li (pydub uchun). FFmpeg bilan bir papkada bo'ladi."""
    if not FFMPEG_LOCATION:
        return None
    parent = Path(FFMPEG_LOCATION).parent
    for name in ("ffprobe.exe", "ffprobe"):
        p = parent / name
        if p.is_file():
            return str(p.resolve())
    if shutil.which("ffprobe"):
        return str(Path(shutil.which("ffprobe")).resolve())
    return None


FFPROBE_LOCATION = _find_ffprobe_exe()

# Internal limits (invisible to user)
USER_PARALLEL_LIMIT = 2
GLOBAL_PARALLEL_LIMIT = 5
REQUEST_DELAY_SEC = 0.3
REQUEST_DELAY_SECONDS = REQUEST_DELAY_SEC
