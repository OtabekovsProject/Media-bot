"""Shazam: recognize from audio, video, voice. Show result + inline (YouTube, 10 variants, Details)."""
import logging
from pathlib import Path

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile

from config import TEMP_DIR, MAX_FILE_SIZE_BYTES
from database import get_db
from services import ShazamService, YouTubeService
from keyboards.inline import build_shazam_result_keyboard, build_variants_keyboard
from utils.locales import get_text
from utils.queue_manager import queue_manager
from utils.cleanup import cleanup_temp_file
from utils.shazam_cache import get_track, set_track
from utils.filename import sanitize_audio_filename

router = Router(name="shazam")
shazam_svc = ShazamService()
youtube_svc = YouTubeService()
logger = logging.getLogger(__name__)


async def _download_audio_from_telegram(message: Message) -> Path | None:
    """Download audio/video/voice/video_note to temp file. Returns path or None."""
    file = None
    if message.audio:
        file = message.audio
    elif message.video:
        file = message.video
    elif message.video_note:
        file = message.video_note
    elif message.voice:
        file = message.voice
    if not file or file.file_size and file.file_size > MAX_FILE_SIZE_BYTES:
        return None
    bot = message.bot
    tg_file = await bot.get_file(file.file_id)
    ext = "ogg" if message.voice else "m4a"
    path = TEMP_DIR / f"shazam_{message.from_user.id}_{message.message_id}.{ext}"
    await bot.download_file(tg_file.file_path, path)
    return path


def _track_display_info(track: dict) -> tuple[str, str, str, str, str]:
    title = track.get("title") or "Unknown"
    subtitle = track.get("subtitle") or "Unknown"
    album = "Unknown"
    genre = "Unknown"
    year = "—"
    for section in (track.get("sections") or []):
        for meta in (section.get("metadata") or []):
            if meta.get("title") == "Album":
                album = meta.get("text", "Unknown")
            elif meta.get("title") == "Genre":
                genre = meta.get("text", "Unknown")
            elif meta.get("title") == "Released":
                year = meta.get("text", "—")
    return title, subtitle, album, genre, year


@router.message(F.audio | F.video | F.video_note | F.voice)
async def on_audio_or_video(message: Message) -> None:
    if not message.from_user:
        return
    user_id = message.from_user.id
    try:
        db = get_db()
        lang = await db.get_user_language(user_id)
        status = await message.answer("⏳", parse_mode="HTML")
        path = await _download_audio_from_telegram(message)
        if not path:
            await status.edit_text(get_text(lang, "file_too_big"), parse_mode="HTML")
            return
        try:
            track = await shazam_svc.recognize_file_thorough(path)
        finally:
            cleanup_temp_file(path)
        if not track:
            await status.edit_text(get_text(lang, "not_found"), parse_mode="HTML")
            return
        title, artist, album, genre, year = _track_display_info(track)
        track_id = track.get("key") or track.get("title", "") or "unknown"
        set_track(user_id, str(track_id), track)
        text = get_text(
            lang,
            "shazam_result",
            title=title,
            artist=artist,
            album=album,
            genre=genre,
            year=year,
        )
        await status.edit_text(
            text,
            reply_markup=build_shazam_result_keyboard(str(track_id), lang),
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error("shazam: %s", e)
        try:
            db = get_db()
            lang = await db.get_user_language(user_id)
            await message.answer(get_text(lang, "error_friendly"), parse_mode="HTML")
        except Exception:
            pass


@router.callback_query(F.data.startswith("shazam_yt:"))
async def shazam_download_yt(callback: CallbackQuery) -> None:
    await callback.answer()
    track_id = callback.data.split("shazam_yt:", 1)[1]
    user_id = callback.from_user.id
    db = get_db()
    lang = await db.get_user_language(user_id)
    track = get_track(user_id, track_id)
    if not track:
        await callback.message.edit_text(get_text(lang, "error_friendly"), parse_mode="HTML")
        return
    title = track.get("title") or "Unknown"
    artist = track.get("subtitle") or "Unknown"
    query = f"{artist} {title}"
    await callback.message.edit_text("⏳", parse_mode="HTML")
    try:
        async with queue_manager(user_id):
            results = await youtube_svc.search(query, max_results=1)
            if not results:
                await callback.message.edit_text(get_text(lang, "error_friendly"), parse_mode="HTML")
                return
            vid = results[0].get("id") or results[0].get("video_id")
            url = f"https://www.youtube.com/watch?v={vid}"
            🎧Audio_path, thumb_path = await youtube_svc.download_🎧Audio_with_cover(
                url, f"shazam_yt_{user_id}_{callback.message.message_id}", title, artist, ""
            )
            if 🎧Audio_path and 🎧Audio_path.exists():
                try:
                    fname = sanitize_audio_filename(title, artist)
                    audio_file = BufferedInputFile(🎧Audio_path.read_bytes(), filename=fname)
                    caption = get_text(lang, "🎧Audio_caption", title=title, artist=artist, album="", duration="")
                    await callback.message.delete()
                    await callback.message.answer_audio(audio_file, caption=caption, parse_mode="HTML")
                finally:
                    cleanup_temp_file(🎧Audio_path)
                    cleanup_temp_file(thumb_path)
            else:
                await callback.message.edit_text(get_text(lang, "error_friendly"), parse_mode="HTML")
    except Exception as e:
        logger.error("shazam_yt: %s", e)
        await callback.message.edit_text(get_text(lang, "error_friendly"), parse_mode="HTML")


@router.callback_query(F.data.startswith("shazam_var:"))
async def shazam_ten_variants(callback: CallbackQuery) -> None:
    await callback.answer()
    track_id = callback.data.split("shazam_var:", 1)[1]
    user_id = callback.from_user.id
    db = get_db()
    lang = await db.get_user_language(user_id)
    track = get_track(user_id, track_id)
    if not track:
        await callback.message.edit_text(get_text(lang, "error_friendly"), parse_mode="HTML")
        return
    title = track.get("title") or "Unknown"
    artist = track.get("subtitle") or "Unknown"
    query = f"{artist} {title}"
    await callback.message.edit_text("⏳", parse_mode="HTML")
    try:
        async with queue_manager(user_id):
            variants = await youtube_svc.search(query, max_results=10)
            if not variants:
                await callback.message.edit_text(get_text(lang, "error_friendly"), parse_mode="HTML")
                return
            text = get_text(lang, "variants_title")
            await callback.message.edit_text(
                text,
                reply_markup=build_variants_keyboard(variants, query),
                parse_mode="HTML",
            )
    except Exception as e:
        logger.error("shazam_var: %s", e)
        await callback.message.edit_text(get_text(lang, "error_friendly"), parse_mode="HTML")


@router.callback_query(F.data.startswith("shazam_det:"))
async def shazam_details(callback: CallbackQuery) -> None:
    await callback.answer(get_text("uz", "details"), show_alert=False)
