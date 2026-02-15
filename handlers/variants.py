"""10 variants: user chose one → download that YouTube as 🎧Audio."""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile

from database import get_db
from services import YouTubeService
from utils.locales import get_text
from utils.queue_manager import queue_manager
from utils.cleanup import cleanup_temp_file
from utils.filename import sanitize_audio_filename

router = Router(name="variants")
youtube_svc = YouTubeService()
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("var:"))
async def on_variant_chosen(callback: CallbackQuery) -> None:
    video_id = callback.data.split("var:", 1)[1]
    user_id = callback.from_user.id
    await callback.answer()
    try:
        db = get_db()
        lang = await db.get_user_language(user_id)
        await callback.message.edit_text("⏳", parse_mode="HTML")
        async with queue_manager(user_id):
            url = f"https://www.youtube.com/watch?v={video_id}"
            prefix = f"var_{user_id}_{callback.message.message_id}_{video_id}"
            🎧Audio_path, thumb_path = await youtube_svc.download_🎧Audio_with_cover(
                url, prefix, "", "", ""
            )
            if 🎧Audio_path and 🎧Audio_path.exists():
                try:
                    info = await youtube_svc.get_video_info(video_id)
                    title = (info.get("title") or "Track")[:50]
                    duration = info.get("duration")
                    duration_str = f"{duration // 60}:{duration % 60:02d}" if duration else "—"
                    caption = get_text(
                        lang, "🎧Audio_caption",
                        title=title, artist="", album="", duration=duration_str,
                    )
                    fname = sanitize_audio_filename(title, "")
                    audio_file = BufferedInputFile(🎧Audio_path.read_bytes(), filename=fname)
                    await callback.message.delete()
                    await callback.message.answer_audio(audio_file, caption=caption, parse_mode="HTML")
                finally:
                    cleanup_temp_file(🎧Audio_path)
                    cleanup_temp_file(thumb_path)
            else:
                await callback.message.edit_text(get_text(lang, "error_friendly"), parse_mode="HTML")
    except Exception as e:
        logger.error("variants: %s", e)
        try:
            db = get_db()
            lang = await db.get_user_language(user_id)
            await callback.message.edit_text(get_text(lang, "error_friendly"), parse_mode="HTML")
        except Exception:
            pass
