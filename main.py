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

from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import BOT_TOKEN, ADMIN_ID, FFMPEG_LOCATION, FFPROBE_LOCATION, PORT, WEBHOOK_URL, WEBHOOK_PATH

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


def _check_ffmpeg() -> bool:
    """FFmpeg mavjudligini tekshirish (FFMPEG_LOCATION = exe yo'li)."""
    if FFMPEG_LOCATION and os.path.isfile(FFMPEG_LOCATION):
        return True
    return shutil.which("ffmpeg") is not None


async def on_startup(bot: Bot) -> None:
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
    
    dp.include_router(admin_router)
    dp.include_router(search_router)
    dp.include_router(start_router)
    dp.include_router(language_router)
    dp.include_router(youtube_mp3_router)
    dp.include_router(media_router)
    dp.include_router(shazam_router)
    dp.include_router(variants_router)

    if WEBHOOK_URL:
        # Webhook mode (Render, Railway, etc.)
        async def on_startup_webhook(bot: Bot) -> None:
            await on_startup(bot)
            await bot.set_webhook(f"{WEBHOOK_URL}{WEBHOOK_PATH}")

        async def on_shutdown_webhook(bot: Bot) -> None:
            await on_shutdown(bot)
            await bot.delete_webhook()

        dp.startup.register(on_startup_webhook)
        dp.shutdown.register(on_shutdown_webhook)

        app = web.Application()
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
        )
        webhook_requests_handler.register(app, path=WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)
        
        # Health check for Render
        async def health_check(request):
            return web.Response(text="OK")
        
        app.router.add_get("/", health_check)
        app.router.add_get("/health", health_check)

        web.run_app(app, host="0.0.0.0", port=PORT if PORT > 0 else 8080)
    else:
        # Polling mode (Local)
        try:
            asyncio.run(dp.start_polling(bot))
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
