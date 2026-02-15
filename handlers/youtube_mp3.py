"""YouTube link → 3 ta tanlash: 🎧Audio, Video, 🎵Musiqasi. Inline tugmalar qoladi."""
import logging
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from database import get_db
from services import YouTubeService, ShazamService
from keyboards.inline import build_shazam_result_keyboard
from utils.locales import get_text
from utils.queue_manager import queue_manager
from utils.cleanup import cleanup_temp_file
from utils.url_extract import get_youtube_id_from_message
from utils.shazam_cache import set_track
from utils.filename import sanitize_audio_filename

router = Router(name="youtube_🎧Audio")
youtube_svc = YouTubeService()
shazam_svc = ShazamService()
logger = logging.getLogger(__name__)


def _track_display_info(track: dict) -> tuple[str, str, str, str, str]:
    title = track.get("title") or "Unknown"
    subtitle = track.get("subtitle") or "Unknown"
    album, genre, year = "Unknown", "Unknown", "—"
    for section in (track.get("sections") or []):
        for meta in (section.get("metadata") or []):
            if meta.get("title") == "Album":
                album = meta.get("text", "Unknown")
            elif meta.get("title") == "Genre":
                genre = meta.get("text", "Unknown")
            elif meta.get("title") == "Released":
                year = meta.get("text", "—")
    return title, subtitle, album, genre, year


def _build_yt_choice_keyboard(vid: str, lang: str):
    """3 ta tugma: 🎧Audio, Video, 🎵Musiqasi."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎧Audio", callback_data=f"yt_🎧Audio:{vid}"),
        InlineKeyboardButton(text="📹 Video", callback_data=f"yt_vid:{vid}"),
        InlineKeyboardButton(text=get_text(lang, "find_full_song"), callback_data=f"yt_shazam:{vid}"),
    )
    return builder.as_markup()

def _has_youtube_link(message: Message) -> bool:
    """Xabar matnida yoki caption/entity da YouTube link bormi."""
    return get_youtube_id_from_message(message) is not None


@router.message(F.text | F.caption, _has_youtube_link)
async def on_youtube_link(message: Message) -> None:
    """User sent YouTube link: send ⏳ then offer 🎧Audio or Video."""
    vid = get_youtube_id_from_message(message)
    if not vid:
        return
    user_id = message.from_user.id
    try:
        db = get_db()
        lang = await db.get_user_language(user_id)
        status = await message.answer("⏳", parse_mode="HTML")
        url = f"https://www.youtube.com/watch?v={vid}"
        text = get_text(lang, "send_yt_for_🎧Audio") + "\n\n👇 " + get_text(lang, "choose")
        await status.edit_text(text, reply_markup=_build_yt_choice_keyboard(vid, lang), parse_mode="HTML")
    except Exception as e:
        logger.error("youtube_link: %s", e)
        try:
            db = get_db()
            lang = await db.get_user_language(user_id)
            await message.answer(get_text(lang, "error_friendly"), parse_mode="HTML")
        except Exception:
            pass


@router.callback_query(F.data.startswith("yt_🎧Audio:"))
async def do_🎧Audio(callback: CallbackQuery) -> None:
    vid = callback.data.split("yt_🎧Audio:", 1)[1]
    user_id = callback.from_user.id
    await callback.answer()
    try:
        db = get_db()
        lang = await db.get_user_language(user_id)
        await callback.message.edit_text("⏳", parse_mode="HTML")
        url = f"https://www.youtube.com/watch?v={vid}"
        async with queue_manager(user_id):
            prefix = f"yt_🎧Audio_{user_id}_{callback.message.message_id}"
            🎧Audio_path, thumb_path = await youtube_svc.download_🎧Audio_with_cover(
                url, prefix, "", "", ""
            )
            if 🎧Audio_path and 🎧Audio_path.exists():
                try:
                    info = await youtube_svc.get_video_info(vid)
                    title = (info.get("title") or "Track")[:50]
                    duration = info.get("duration")
                    duration_str = f"{duration // 60}:{duration % 60:02d}" if duration else "—"
                    caption = get_text(
                        lang, "🎧Audio_caption",
                        title=title, artist="", album="", duration=duration_str,
                    )
                    fname = sanitize_audio_filename(title, "")
                    audio_file = BufferedInputFile(🎧Audio_path.read_bytes(), filename=fname)
                    await callback.message.answer_audio(audio_file, caption=caption, parse_mode="HTML")
                    await callback.message.edit_text(
                        get_text(lang, "yt_done_keep"),
                        reply_markup=_build_yt_choice_keyboard(vid, lang),
                        parse_mode="HTML",
                    )
                finally:
                    cleanup_temp_file(🎧Audio_path)
                    cleanup_temp_file(thumb_path)
            else:
                await callback.message.edit_text(
                    get_text(lang, "error_friendly"),
                    reply_markup=_build_yt_choice_keyboard(vid, lang),
                    parse_mode="HTML",
                )
    except Exception as e:
        logger.error("yt_🎧Audio: %s", e)
        try:
            db = get_db()
            lang = await db.get_user_language(user_id)
            await callback.message.edit_text(
                get_text(lang, "error_friendly"),
                reply_markup=_build_yt_choice_keyboard(vid, lang),
                parse_mode="HTML",
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("yt_vid:"))
async def do_video(callback: CallbackQuery) -> None:
    vid = callback.data.split("yt_vid:", 1)[1]
    user_id = callback.from_user.id
    await callback.answer()
    try:
        db = get_db()
        lang = await db.get_user_language(user_id)
        await callback.message.edit_text("⏳", parse_mode="HTML")
        url = f"https://www.youtube.com/watch?v={vid}"
        async with queue_manager(user_id):
            prefix = f"yt_vid_{user_id}_{callback.message.message_id}"
            path = await youtube_svc.download_video(url, prefix)
            if path and path.exists():
                try:
                    await callback.message.answer_video(FSInputFile(path))
                    await callback.message.edit_text(
                        get_text(lang, "yt_done_keep"),
                        reply_markup=_build_yt_choice_keyboard(vid, lang),
                        parse_mode="HTML",
                    )
                finally:
                    cleanup_temp_file(path)
            else:
                await callback.message.edit_text(
                    get_text(lang, "error_friendly"),
                    reply_markup=_build_yt_choice_keyboard(vid, lang),
                    parse_mode="HTML",
                )
    except Exception as e:
        logger.error("yt_vid: %s", e)
        try:
            db = get_db()
            lang = await db.get_user_language(user_id)
            await callback.message.edit_text(
                get_text(lang, "error_friendly"),
                reply_markup=_build_yt_choice_keyboard(vid, lang),
                parse_mode="HTML",
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("yt_shazam:"))
async def do_yt_shazam(callback: CallbackQuery) -> None:
    """Video ichidagi qo'shiqni Shazam orqali topib, to'liq trek taklif qilish."""
    vid = callback.data.split("yt_shazam:", 1)[1]
    user_id = callback.from_user.id
    await callback.answer()
    try:
        db = get_db()
        lang = await db.get_user_language(user_id)
        await callback.message.edit_text("⏳", parse_mode="HTML")
        url = f"https://www.youtube.com/watch?v={vid}"
        async with queue_manager(user_id):
            prefix = f"yt_shazam_{user_id}_{callback.message.message_id}"
            🎧Audio_path, thumb_path = await youtube_svc.download_🎧Audio_with_cover(url, prefix, "", "", "")
            if not 🎧Audio_path or not 🎧Audio_path.exists():
                await callback.message.edit_text(
                    get_text(lang, "error_friendly"),
                    reply_markup=_build_yt_choice_keyboard(vid, lang),
                    parse_mode="HTML",
                )
                return
            try:
                track = await shazam_svc.recognize_file_thorough(🎧Audio_path)
            finally:
                cleanup_temp_file(🎧Audio_path)
                cleanup_temp_file(thumb_path)
            if not track:
                await callback.message.edit_text(
                    get_text(lang, "not_found"),
                    reply_markup=_build_yt_choice_keyboard(vid, lang),
                    parse_mode="HTML",
                )
                return
            track_id = track.get("key") or track.get("title", "") or "unknown"
            set_track(user_id, str(track_id), track)
            title, artist, album, genre, year = _track_display_info(track)
            text = get_text(
                lang, "shazam_result",
                title=title, artist=artist, album=album, genre=genre, year=year,
            )
            await callback.message.edit_text(
                text,
                reply_markup=build_shazam_result_keyboard(str(track_id), lang),
                parse_mode="HTML",
            )
    except Exception as e:
        logger.error("yt_shazam: %s", e)
        try:
            db = get_db()
            lang = await db.get_user_language(user_id)
            await callback.message.edit_text(
                get_text(lang, "error_friendly"),
                reply_markup=_build_yt_choice_keyboard(vid, lang),
                parse_mode="HTML",
            )
        except Exception:
            pass
