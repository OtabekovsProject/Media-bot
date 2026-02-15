"""Instagram, TikTok, Pinterest, Facebook — link yuborilgach tanlash menyusi (Video / 🎧Audio / Qo'shiqni topish)."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from database import get_db
from services import MediaDownloaderService, ShazamService
from keyboards.inline import build_shazam_result_keyboard
from utils.locales import get_text
from utils.queue_manager import queue_manager
from utils.cleanup import cleanup_temp_file
from utils.url_extract import get_first_url_from_message, get_youtube_id_from_message
from utils.shazam_cache import set_track
from utils.filename import sanitize_audio_filename

router = Router(name="media")
media_svc = MediaDownloaderService()
shazam_svc = ShazamService()
logger = logging.getLogger(__name__)

# (user_id, message_id) -> url
_media_pending: dict[tuple[int, int], str] = {}


def _build_media_keyboard(lang: str):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📹 Video", callback_data="md_v"),
        InlineKeyboardButton(text="🎧Audio", callback_data="md_🎧Audio"),
        InlineKeyboardButton(text=get_text(lang, "find_full_song"), callback_data="md_s"),
    )
    return builder.as_markup()


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


def _has_non_yt_link(message: Message) -> bool:
    if get_youtube_id_from_message(message):
        return False
    return get_first_url_from_message(message) is not None


def _send_media_by_path(message: Message, path):
    """Fayl turiga qarab video yoki document yuboradi. FSInputFile – katta fayllar xotiraga yuklanmaydi."""
    video_ext = (".mp4", ".webm", ".mov", ".mkv", ".avi")
    inp = FSInputFile(path)
    if path.suffix.lower() in video_ext:
        return message.answer_video(inp)
    return message.answer_document(inp)


@router.message(F.text | F.caption, _has_non_yt_link)
async def on_link(message: Message) -> None:
    url = get_first_url_from_message(message)
    if not url:
        return
    platform = media_svc.detect_platform(url)
    if not platform:
        return
    user_id = message.from_user.id
    try:
        db = get_db()
        lang = await db.get_user_language(user_id)
        status = await message.answer("⏳", parse_mode="HTML")
        _media_pending[(user_id, status.message_id)] = url
        text = get_text(lang, "media_choose", platform=platform)
        await status.edit_text(text, reply_markup=_build_media_keyboard(lang), parse_mode="HTML")
    except Exception as e:
        logger.error("media_menu: %s", e)
        try:
            await message.answer(get_text("uz", "error_friendly"), parse_mode="HTML")
        except Exception:
            pass


def _get_pending(callback: CallbackQuery) -> str | None:
    key = (callback.from_user.id, callback.message.message_id)
    return _media_pending.pop(key, None)


def _put_pending(user_id: int, message_id: int, url: str) -> None:
    _media_pending[(user_id, message_id)] = url


@router.callback_query(F.data == "md_v")
async def on_media_video(callback: CallbackQuery) -> None:
    url = _get_pending(callback)
    if not url:
        await callback.answer(get_text("uz", "error_friendly"), show_alert=True)
        return
    await callback.answer()
    user_id = callback.from_user.id
    try:
        db = get_db()
        lang = await db.get_user_language(user_id)
        await callback.message.edit_text("⏳", parse_mode="HTML")
        async with queue_manager(user_id):
            prefix = f"md_v_{user_id}_{callback.message.message_id}"
            path = await media_svc.download_video_or_image(url, prefix)
            if path and path.exists():
                try:
                    await _send_media_by_path(callback.message, path)
                    await callback.message.edit_text(
                        get_text(lang, "yt_done_keep"),
                        reply_markup=_build_media_keyboard(lang),
                        parse_mode="HTML",
                    )
                finally:
                    cleanup_temp_file(path)
                _put_pending(user_id, callback.message.message_id, url)
            else:
                await callback.message.edit_text(
                    get_text(lang, "error_friendly"),
                    reply_markup=_build_media_keyboard(lang),
                    parse_mode="HTML",
                )
                _put_pending(user_id, callback.message.message_id, url)
    except Exception as e:
        logger.error("md_v: %s", e)
        try:
            lang = await get_db().get_user_language(user_id)
            await callback.message.edit_text(get_text(lang, "error_friendly"), parse_mode="HTML")
            _put_pending(user_id, callback.message.message_id, url)
        except Exception:
            pass


@router.callback_query(F.data == "md_🎧Audio")
async def on_media_🎧Audio(callback: CallbackQuery) -> None:
    url = _get_pending(callback)
    if not url:
        await callback.answer(get_text("uz", "error_friendly"), show_alert=True)
        return
    await callback.answer()
    user_id = callback.from_user.id
    try:
        db = get_db()
        lang = await db.get_user_language(user_id)
        await callback.message.edit_text("⏳", parse_mode="HTML")
        async with queue_manager(user_id):
            prefix = f"md_🎧Audio_{user_id}_{callback.message.message_id}"
            path = await media_svc.download_as_🎧Audio(url, prefix)
            if path and path.exists():
                try:
                    fname = sanitize_audio_filename("Track", "")
                    audio_file = FSInputFile(path)
                    caption = get_text(lang, "🎧Audio_caption", title="Track", artist="", album="", duration="")
                    await callback.message.answer_audio(audio_file, caption=caption, parse_mode="HTML")
                    await callback.message.edit_text(
                        get_text(lang, "yt_done_keep"),
                        reply_markup=_build_media_keyboard(lang),
                        parse_mode="HTML",
                    )
                finally:
                    cleanup_temp_file(path)
                _put_pending(user_id, callback.message.message_id, url)
            else:
                await callback.message.edit_text(
                    get_text(lang, "error_friendly"),
                    reply_markup=_build_media_keyboard(lang),
                    parse_mode="HTML",
                )
                _put_pending(user_id, callback.message.message_id, url)
    except Exception as e:
        logger.error("md_🎧Audio: %s", e)
        try:
            lang = await get_db().get_user_language(user_id)
            await callback.message.edit_text(get_text(lang, "error_friendly"), parse_mode="HTML")
            _put_pending(user_id, callback.message.message_id, url)
        except Exception:
            pass


@router.callback_query(F.data == "md_s")
async def on_media_shazam(callback: CallbackQuery) -> None:
    url = _get_pending(callback)
    if not url:
        await callback.answer(get_text("uz", "error_friendly"), show_alert=True)
        return
    await callback.answer()
    user_id = callback.from_user.id
    try:
        db = get_db()
        lang = await db.get_user_language(user_id)
        await callback.message.edit_text("⏳", parse_mode="HTML")
        async with queue_manager(user_id):
            prefix = f"md_s_{user_id}_{callback.message.message_id}"
            🎧Audio_path = await media_svc.download_as_🎧Audio(url, prefix)
            if not 🎧Audio_path or not 🎧Audio_path.exists():
                await callback.message.edit_text(
                    get_text(lang, "error_friendly"),
                    reply_markup=_build_media_keyboard(lang),
                    parse_mode="HTML",
                )
                _put_pending(user_id, callback.message.message_id, url)
                return
            try:
                track = await shazam_svc.recognize_file_thorough(🎧Audio_path)
            finally:
                cleanup_temp_file(🎧Audio_path)
            if not track:
                await callback.message.edit_text(
                    get_text(lang, "not_found"),
                    reply_markup=_build_media_keyboard(lang),
                    parse_mode="HTML",
                )
                _put_pending(user_id, callback.message.message_id, url)
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
        logger.error("md_s: %s", e)
        try:
            lang = await get_db().get_user_language(user_id)
            await callback.message.edit_text(get_text(lang, "error_friendly"), parse_mode="HTML")
            _put_pending(user_id, callback.message.message_id, url)
        except Exception:
            pass
