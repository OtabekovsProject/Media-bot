"""Majburiy obuna: kanal(lar)ga obuna bo'lmagan foydalanuvchi botdan foydalana olmaydi."""
import logging
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from aiogram.enums import ChatMemberStatus

from database import get_db
from utils.locales import get_text

logger = logging.getLogger(__name__)


async def _is_member(bot, chat_id: int, user_id: int) -> bool:
    try:
        m = await bot.get_chat_member(chat_id, user_id)
        return m.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.CREATOR,
            ChatMemberStatus.RESTRICTED,
        )
    except Exception:
        return False


class SubscriptionMiddleware(BaseMiddleware):
    """Har bir xabar/callback dan oldin kanal(lar)ga obunani tekshiradi."""

    async def __call__(self, handler, event: TelegramObject, data: dict):
        bot = data["bot"]
        user_id = None
        chat_id = None
        if isinstance(event, Message) and event.from_user:
            raw = (event.text or "").strip()
            if raw.startswith("/admin"):
                return await handler(event, data)
            # /start (va /start ref...) – oddiy va admin ham darhol til tanlash oladi
            if raw == "/start" or raw.startswith("/start "):
                return await handler(event, data)
            user_id = event.from_user.id
            chat_id = event.chat.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id
            chat_id = event.message.chat.id if event.message else None
            if event.data == "sub_check":
                return await handler(event, data)
            # Til tanlash (lang:uz, lang:ru, lang:en) – obunasiz ham ishlashi uchun
            if event.data and event.data.startswith("lang:"):
                return await handler(event, data)
        if not user_id or not chat_id:
            return await handler(event, data)

        try:
            db = get_db()
            channels = await db.get_channels()
        except Exception:
            logger.error("subscription get_channels")
            return await handler(event, data)
        if not channels:
            return await handler(event, data)

        try:
            for ch in channels:
                if not await _is_member(bot, ch["chat_id"], user_id):
                    lang = await db.get_user_language(user_id)
                    lines = []
                    from aiogram.utils.keyboard import InlineKeyboardBuilder
                    from aiogram.types import InlineKeyboardButton
                    builder = InlineKeyboardBuilder()
                    for c in channels:
                        if not await _is_member(bot, c["chat_id"], user_id):
                            title = c.get("title") or f"Kanal {c['chat_id']}"
                            link = c.get("invite_link") or (f"https://t.me/{c.get('username', '').lstrip('@')}" if c.get("username") else None)
                            if link:
                                builder.row(InlineKeyboardButton(text=f"📢 {title[:30]}", url=link))
                            lines.append(f"• {title}")
                    builder.row(InlineKeyboardButton(text=get_text(lang, "subscribe_check"), callback_data="sub_check"))
                    text = get_text(lang, "subscribe_required", channels="\n".join(lines) if lines else get_text(lang, "no_channels"))
                    if isinstance(event, CallbackQuery):
                        try:
                            await event.answer()
                            await event.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
                        except Exception:
                            await event.message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
                    else:
                        await event.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
                    return
        except Exception:
            logger.error("subscription check")
            return await handler(event, data)
        return await handler(event, data)
