"""YouTube link -> MP3 with cover."""
import re

from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from aiogram import Bot

from database import get_user_language, log_action
from services.queue import task_queue
from services.youtube_service import youtube_to_mp3
from utils.i18n import get_text

router = Router(name="youtube")

YT_PATTERN = re.compile(
    r"(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]+",
    re.IGNORECASE,
)


@router.message(F.text, F.text.regexp(YT_PATTERN))
async def on_youtube_link(message: Message, bot: Bot) -> None:
    """YouTube link -> download as MP3 with cover."""
    user_id = message.from_user.id if message.from_user else 0
    lang = get_user_language(user_id)
    url = (message.text or "").strip()
    if not url:
        return
    log_action(user_id, "youtube_link")
    status = await message.answer(get_text(lang, "loading"), parse_mode="HTML")
    try:
        mp3_path, cover_path, info = await task_queue.run(
            user_id,
            lambda: youtube_to_mp3(url, user_id),
        )
        if not mp3_path or not mp3_path.exists():
            await status.edit_text(get_text(lang, "error_download"), parse_mode="HTML")
            return
        title = info.get("title", "Unknown")
        artist = info.get("artist", "Unknown")
        album = info.get("album", "—")
        duration = info.get("duration", "—")
        caption = get_text(lang, "mp3_caption", title=title, artist=artist, album=album, duration=duration)
        with open(mp3_path, "rb") as f:
            audio_data = f.read()
        if cover_path and cover_path.exists():
            with open(cover_path, "rb") as cf:
                thumb = cf.read()
            await message.answer_audio(
                BufferedInputFile(audio_data, filename="audio.mp3"),
                title=title[:64],
                performer=artist[:64],
                thumb=BufferedInputFile(thumb, "cover.jpg"),
                caption=caption,
                parse_mode="HTML",
            )
        else:
            await message.answer_audio(
                BufferedInputFile(audio_data, filename="audio.mp3"),
                title=title[:64],
                performer=artist[:64],
                caption=caption,
                parse_mode="HTML",
            )
        await status.edit_text(get_text(lang, "ready_mp3"), parse_mode="HTML")
        from utils.cleanup import cleanup_user_temp
        cleanup_user_temp(user_id)
    except Exception:
        await status.edit_text(get_text(lang, "error_generic"), parse_mode="HTML")
