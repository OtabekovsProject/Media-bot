"""Start and /start command. Obuna tekshiruvi callback."""
import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.exceptions import TelegramBadRequest

from database import get_db
from keyboards.inline import get_language_keyboard
from utils.locales import get_text

router = Router(name="start")
NOT_LINK = ~F.text.regexp(re.compile(r"https?://", re.IGNORECASE))


async def _safe_edit_text(callback: CallbackQuery, text: str, reply_markup=None, parse_mode: str = "HTML"):
    """edit_text chaqiradi; 'message is not modified' xatoligida hech narsa qilmaydi."""
    try:
        if reply_markup is not None:
            await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        else:
            await callback.message.edit_text(text, parse_mode=parse_mode)
    except TelegramBadRequest as e:
        if "message is not modified" not in (e.message or ""):
            raise


@router.callback_query(F.data == "sub_check")
async def on_subscribe_check(callback: CallbackQuery) -> None:
    """«Tekshirish» – obuna bo‘lganligini qayta tekshirish."""
    from aiogram.enums import ChatMemberStatus
    user_id = callback.from_user.id
    db = get_db()
    lang = await db.get_user_language(user_id)
    channels = await db.get_channels()
    if not channels:
        await callback.answer()
        await _safe_edit_text(callback, get_text(lang, "subscribe_ok"))
        return
    not_joined_titles = []
    not_joined_ids = set()
    for ch in channels:
        try:
            m = await callback.bot.get_chat_member(ch["chat_id"], user_id)
            if m.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER, ChatMemberStatus.CREATOR, ChatMemberStatus.RESTRICTED):
                continue
        except Exception:
            pass
        not_joined_ids.add(ch["chat_id"])
        not_joined_titles.append(ch.get("title") or f"Kanal {ch['chat_id']}")
    await callback.answer()
    if not not_joined_titles:
        await _safe_edit_text(callback, get_text(lang, "subscribe_ok"))
    else:
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        from aiogram.types import InlineKeyboardButton
        builder = InlineKeyboardBuilder()
        for c in channels:
            if c["chat_id"] in not_joined_ids:
                link = c.get("invite_link") or (f"https://t.me/{c.get('username', '').lstrip('@')}" if c.get("username") else None)
                if link:
                    builder.row(InlineKeyboardButton(text=f"📢 {(c.get('title') or 'Kanal')[:30]}", url=link))
        builder.row(InlineKeyboardButton(text=get_text(lang, "subscribe_check"), callback_data="sub_check"))
        await _safe_edit_text(
            callback,
            get_text(lang, "subscribe_fail", channels="\n".join(not_joined_titles)),
            reply_markup=builder.as_markup(),
        )


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Birinchi /start: til tanlash. Keyingi /start: faqat xush kelibsiz (til allaqachon tanlangan)."""
    user_id = message.from_user.id if message.from_user else 0
    db = get_db()
    first_name = (message.from_user.first_name or "")[:100] if message.from_user else ""
    username = (message.from_user.username or "")[:100] if message.from_user else ""
    await db.ensure_user(user_id, first_name=first_name, username=username)
    await db.log_action(user_id, "start")
    lang = await db.get_user_language(user_id)
    lang_chosen = await db.get_lang_chosen(user_id)
    if lang_chosen:
        await message.answer(get_text(lang, "welcome_after_lang"), parse_mode="HTML")
    else:
        welcome = get_text(lang, "welcome")
        await message.answer(
            welcome,
            reply_markup=get_language_keyboard(),
            parse_mode="HTML",
        )


# Hint faqat oddiy matn uchun – buyruqlar (/admin, /start va b.) boshqa handlerlarda
@router.message(F.text, NOT_LINK, ~F.text.startswith("/"))
async def hint(message: Message) -> None:
    """Link va buyruq bo'lmagan matn -> hint."""
    user_id = message.from_user.id if message.from_user else 0
    db = get_db()
    lang = await db.get_user_language(user_id)
    await message.answer(get_text(lang, "hint"), parse_mode="HTML")
