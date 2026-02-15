from aiogram import Router, F
from aiogram.types import CallbackQuery

from database import get_db
from utils.locales import get_text

router = Router(name="language")


@router.callback_query(F.data.startswith("lang:"))
async def set_language(callback: CallbackQuery) -> None:
    lang = callback.data.split(":", 1)[1]
    if lang not in ("uz", "ru", "en"):
        await callback.answer()
        return
    user_id = callback.from_user.id
    db = get_db()
    await db.set_user_language(user_id, lang)
    await db.log_action(user_id, f"lang_{lang}")
    text = get_text(lang, "lang_set")
    await callback.message.edit_text(text, parse_mode="HTML")
    welcome = get_text(lang, "welcome_after_lang")
    await callback.message.answer(welcome, parse_mode="HTML")
    await callback.answer()
