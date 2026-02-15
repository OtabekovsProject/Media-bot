"""
Professional Telegram bot: Shazam, YouTube MP3, media download (Instagram, TikTok, Pinterest).
Python 3.11, aiogram 3.x, SQLite, asyncio queue limits.
"""
import asyncio
import logging
import shutil
import os
import warnings

# Pydub ffmpeg va ffprobe ogohlantirishlarini bostirish
warnings.filterwarnings("ignore", message="Couldn't find ffmpeg or avconv", category=RuntimeWarning, module="pydub")
warnings.filterwarnings("ignore", message="Couldn't find ffprobe or avprobe", category=RuntimeWarning, module="pydub")

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, ADMIN_ID, FFMPEG_LOCATION, FFPROBE_LOCATION, PORT

# Pydub uchun ffmpeg va ffprobe yo'llari (ogohlantirishlar chiqmasin)
if FFMPEG_LOCATION and os.path.isfile(FFMPEG_LOCATION):
    try:
        from pydub import AudioSegment
        AudioSegment.converter = FFMPEG_LOCATION
        AudioSegment.ffmpeg = FFMPEG_LOCATION
        if FFPROBE_LOCATION and os.path.isfile(FFPROBE_LOCATION):
            AudioSegment.ffprobe = FFPROBE_LOCATION
    except Exception:
        pass
# ffprobe topilmasa ham PATH ga ffmpeg papkasini qo'shamiz (ffprobe odatda shu yerda)
if FFMPEG_LOCATION:
    ffmpeg_dir = os.path.dirname(FFMPEG_LOCATION)
    if ffmpeg_dir and ffmpeg_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

from database import get_db
from handlers import (
    start_router,
    language_router,
    search_router,
    shazam_router,
    youtube_mp3_router,
    media_router,
    variants_router,
    admin_router,
)
from middlewares.subscription import SubscriptionMiddleware

# Faqat xatoliklar; user_id, chat_id, token terminalda chiqmasin
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logging.getLogger("aiogram").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)


def _run_health_server(port: int) -> None:
    """Portda HTTP server – platforma botni uxlatmasin (Railway, Render va b.)."""
    import threading
    from http.server import HTTPServer, BaseHTTPRequestHandler
    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        def log_message(self, *args):
            pass
    server = HTTPServer(("0.0.0.0", port), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()


def _check_ffmpeg() -> bool:
    """FFmpeg mavjudligini tekshirish (FFMPEG_LOCATION = exe yo'li)."""
    if FFMPEG_LOCATION and os.path.isfile(FFMPEG_LOCATION):
        return True
    return shutil.which("ffmpeg") is not None


async def on_startup(bot: Bot) -> None:
    if PORT > 0:
        _run_health_server(PORT)
    db = get_db()
    await db.connect()
    if not _check_ffmpeg():
        logger.error("FFmpeg topilmadi.")


async def on_shutdown(bot: Bot) -> None:
    db = get_db()
    await db.close()


def main() -> None:
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is required. Set it in .env")
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())
    # Admin state (broadcast, add_admin, add_channel) birinchi – admin xabari boshqa handlerda ushlanmasin
    dp.include_router(admin_router)
    # Qidiruv (matn = qo'shiq nomi) start dan oldin – "Beanie" kabi matn 10 ta variant beradi, hint emas
    dp.include_router(search_router)
    dp.include_router(start_router)
    dp.include_router(language_router)
    dp.include_router(youtube_mp3_router)
    dp.include_router(media_router)
    dp.include_router(shazam_router)
    dp.include_router(variants_router)
    try:
        asyncio.run(dp.start_polling(bot))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
