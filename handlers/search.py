"""Plain text = song name → YouTube search → 10 variants with inline buttons (MP3 with cover on click)."""
import logging
from aiogram import Router, F
from aiogram.types import Message

from database import get_db
from services import YouTubeService
from keyboards.inline import build_variants_keyboard
from utils.locales import get_text
from utils.url_extract import get_first_url_from_message

router = Router(name="search")
youtube_svc = YouTubeService()
logger = logging.getLogger(__name__)


def _is_search_query(message: Message) -> bool:
    text = (message.text or "").strip()
    if len(text) < 2 or text.startswith("/"):
        return False
    return get_first_url_from_message(message) is None


@router.message(F.text, _is_search_query)
async def on_search_query(message: Message) -> None:
    query = (message.text or "").strip()
    if not query:
        return
    user_id = message.from_user.id
    status = None
    try:
        status = await message.answer("⏳", parse_mode="HTML")
        db = get_db()
        lang = await db.get_user_language(user_id)
        variants = await youtube_svc.search(query, max_results=10)
        if not variants:
            await status.edit_text(get_text(lang, "search_nothing"), parse_mode="HTML")
            return
        text = get_text(lang, "search_results", query=query[:50])
        await status.edit_text(
            text,
            reply_markup=build_variants_keyboard(variants, query),
            parse_mode="HTML",
        )
    except Exception:
        logger.error("search")
        try:
            db = get_db()
            lang = await db.get_user_language(user_id)
            err = get_text(lang, "error_friendly")
            if status is not None:
                await status.edit_text(err, parse_mode="HTML")
            else:
                await message.answer(err, parse_mode="HTML")
        except Exception:
            pass
