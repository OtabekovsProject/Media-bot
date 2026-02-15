"""Admin panel: /admin – qat'iy tekshiruv, foydalanuvchilar, broadcast, admin qo'shish, majburiy obuna."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command, BaseFilter

from config import ADMIN_ID
from database import get_db
from utils.locales import get_text

router = Router(name="admin")

# Oddiy "state": admin_id -> "broadcast" | "add_admin" | "add_channel" | "remove_admin"
_admin_state: dict[int, str] = {}
logger = logging.getLogger(__name__)


class AdminStateFilter(BaseFilter):
    """Faqat admin state da bo'lganda (broadcast/add_admin/add_channel) shu handler ishlaydi."""
    async def __call__(self, message: Message) -> bool:
        return message.from_user is not None and message.from_user.id in _admin_state


def _is_admin(user_id: int) -> bool:
    """ADMIN_ID (env) yoki DB dagi admin – faqat shularga ruxsat."""
    return user_id == ADMIN_ID and ADMIN_ID != 0


async def _is_admin_db(user_id: int) -> bool:
    if _is_admin(user_id):
        return True
    db = get_db()
    return await db.is_admin(user_id)


def _admin_panel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=get_text("uz", "admin_users"), callback_data="adm_users"),
        InlineKeyboardButton(text=get_text("uz", "admin_broadcast"), callback_data="adm_broadcast"),
    )
    builder.row(
        InlineKeyboardButton(text=get_text("uz", "admin_add_admin"), callback_data="adm_add"),
        InlineKeyboardButton(text=get_text("uz", "admin_remove_admin"), callback_data="adm_remove"),
    )
    builder.row(
        InlineKeyboardButton(text=get_text("uz", "admin_channels"), callback_data="adm_channels"),
    )
    return builder.as_markup()


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    """Faqat ADMIN_ID yoki DB admins – qat'iy tekshiruv."""
    user_id = message.from_user.id if message.from_user else 0
    if not await _is_admin_db(user_id):
        await message.answer(get_text("uz", "admin_denied"), parse_mode="HTML")
        return
    await message.answer(
        get_text("uz", "admin_panel"),
        reply_markup=_admin_panel_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "adm_back")
async def admin_back(callback: CallbackQuery) -> None:
    if not await _is_admin_db(callback.from_user.id):
        await callback.answer(get_text("uz", "admin_denied"), show_alert=True)
        return
    await callback.answer()
    _admin_state.pop(callback.from_user.id, None)
    await callback.message.edit_text(
        get_text("uz", "admin_panel"),
        reply_markup=_admin_panel_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "adm_users")
async def admin_users(callback: CallbackQuery) -> None:
    if not await _is_admin_db(callback.from_user.id):
        await callback.answer(get_text("uz", "admin_denied"), show_alert=True)
        return
    await callback.answer()
    db = get_db()
    count = await db.get_user_count()
    users = await db.get_all_users()
    max_show = 50
    lines = []
    for u in users[:max_show]:
        name = (u["first_name"] or "—").replace("<", "").replace(">", "")
        username = (u["username"] or "—").strip()
        if username != "—" and not username.startswith("@"):
            username = f"@{username}"
        lines.append(f"• {name} | {username} | ID: <code>{u['user_id']}</code>")
    list_text = "\n".join(lines) if lines else "—"
    if len(users) > max_show:
        list_text += f"\n\n... va yana {len(users) - max_show} ta"
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text("uz", "admin_back"), callback_data="adm_back"))
    await callback.message.edit_text(
        get_text("uz", "admin_users_list", count=count, list=list_text),
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "adm_broadcast")
async def admin_broadcast_start(callback: CallbackQuery) -> None:
    if not await _is_admin_db(callback.from_user.id):
        await callback.answer(get_text("uz", "admin_denied"), show_alert=True)
        return
    await callback.answer()
    uid = callback.from_user.id
    _admin_state[uid] = "broadcast"
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text("uz", "admin_back"), callback_data="adm_back"))
    await callback.message.edit_text(
        get_text("uz", "admin_send_broadcast"),
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "adm_add")
async def admin_add_start(callback: CallbackQuery) -> None:
    if not await _is_admin_db(callback.from_user.id):
        await callback.answer(get_text("uz", "admin_denied"), show_alert=True)
        return
    await callback.answer()
    uid = callback.from_user.id
    _admin_state[uid] = "add_admin"
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text("uz", "admin_back"), callback_data="adm_back"))
    await callback.message.edit_text(
        get_text("uz", "admin_send_user_id"),
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "adm_remove")
async def admin_remove_start(callback: CallbackQuery) -> None:
    if not await _is_admin_db(callback.from_user.id):
        await callback.answer(get_text("uz", "admin_denied"), show_alert=True)
        return
    await callback.answer()
    uid = callback.from_user.id
    _admin_state[uid] = "remove_admin"
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text("uz", "admin_back"), callback_data="adm_back"))
    await callback.message.edit_text(
        get_text("uz", "admin_send_user_id_remove"),
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


def _extract_user_id(message: Message) -> int | None:
    if message.forward_from and message.forward_from.id:
        return message.forward_from.id
    if message.text and message.text.strip().isdigit():
        return int(message.text.strip())
    return None


@router.message((F.text | F.photo | F.video | F.document | F.voice), AdminStateFilter())
async def admin_state_message(message: Message) -> None:
    uid = message.from_user.id if message.from_user else 0
    state = _admin_state.pop(uid, None)
    if not state:
        return
    if not await _is_admin_db(uid):
        await message.answer(get_text("uz", "admin_denied"), parse_mode="HTML")
        return
    db = get_db()
    if state == "broadcast":
        user_ids = await db.get_all_user_ids()
        sent, failed = 0, 0
        for u in user_ids:
            try:
                await message.copy_to(u)
                sent += 1
            except Exception:
                failed += 1
        await message.answer(
            get_text("uz", "admin_broadcast_done", sent=sent, failed=failed),
            parse_mode="HTML",
        )
        await message.answer(get_text("uz", "admin_panel"), reply_markup=_admin_panel_keyboard(), parse_mode="HTML")
        return
    if state == "add_admin":
        target_id = _extract_user_id(message)
        if target_id is None:
            await message.answer(get_text("uz", "error_friendly") + "\nID raqam yoki forward qiling.", parse_mode="HTML")
            _admin_state[uid] = "add_admin"
            return
        await db.add_admin(target_id, uid)
        await message.answer(get_text("uz", "admin_added"), parse_mode="HTML")
        await message.answer(get_text("uz", "admin_panel"), reply_markup=_admin_panel_keyboard(), parse_mode="HTML")
        return
    if state == "remove_admin":
        target_id = _extract_user_id(message)
        if target_id is None:
            await message.answer(get_text("uz", "error_friendly") + "\nID raqam yoki forward qiling.", parse_mode="HTML")
            _admin_state[uid] = "remove_admin"
            return
        if target_id == ADMIN_ID and ADMIN_ID != 0:
            await message.answer("⛔ Asosiy adminni (ADMIN_ID) o'chirib bo'lmaydi.", parse_mode="HTML")
            _admin_state[uid] = "remove_admin"
            return
        await db.remove_admin(target_id)
        await message.answer(get_text("uz", "admin_removed"), parse_mode="HTML")
        await message.answer(get_text("uz", "admin_panel"), reply_markup=_admin_panel_keyboard(), parse_mode="HTML")
        return
    if state == "add_channel":
        # Kanaldan forward qilingan xabar bo'lsa – chat_id va title olamiz
        if message.forward_from_chat and message.forward_from_chat.id:
            chat_id = message.forward_from_chat.id
            title = message.forward_from_chat.title or str(chat_id)
            username = getattr(message.forward_from_chat, "username", None) or ""
            invite = None
            try:
                invite = (await message.bot.create_chat_invite_link(chat_id)).invite_link
            except Exception:
                if username:
                    invite = f"https://t.me/{username}"
            await db.add_channel(chat_id=chat_id, title=title, username=username or "", invite_link=invite)
            await message.answer(get_text("uz", "admin_channel_added"), parse_mode="HTML")
            _admin_state.pop(uid, None)
            await message.answer(get_text("uz", "admin_panel"), reply_markup=_admin_panel_keyboard(), parse_mode="HTML")
            return
        text = (message.text or message.caption or "").strip()
        if not text:
            await message.answer(get_text("uz", "error_friendly") + "\nKanal @username, link yoki kanaldan xabar forward qiling.", parse_mode="HTML")
            _admin_state[uid] = "add_channel"
            return
        # @username yoki t.me/... link
        username = None
        if "t.me/" in text:
            username = text.split("t.me/")[-1].split("?")[0].strip("/")
        elif text.startswith("@"):
            username = text.lstrip("@")
        if not username:
            await message.answer(get_text("uz", "admin_send_channel"), parse_mode="HTML")
            _admin_state[uid] = "add_channel"
            return
        try:
            chat = await message.bot.get_chat(f"@{username}")
            invite = None
            try:
                invite = (await message.bot.create_chat_invite_link(chat.id)).invite_link
            except Exception:
                if chat.username:
                    invite = f"https://t.me/{chat.username}"
            await db.add_channel(
                chat_id=chat.id,
                title=chat.title or str(chat.id),
                username=chat.username or "",
                invite_link=invite,
            )
            await message.answer(get_text("uz", "admin_channel_added"), parse_mode="HTML")
        except Exception:
            logger.error("add_channel")
            await message.answer(get_text("uz", "error_friendly") + "\n(Bot kanalda admin bo'lishi kerak.)", parse_mode="HTML")
        _admin_state.pop(uid, None)
        await message.answer(get_text("uz", "admin_panel"), reply_markup=_admin_panel_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "adm_channels")
async def admin_channels_list(callback: CallbackQuery) -> None:
    if not await _is_admin_db(callback.from_user.id):
        await callback.answer(get_text("uz", "admin_denied"), show_alert=True)
        return
    await callback.answer()
    _admin_state.pop(callback.from_user.id, None)
    db = get_db()
    channels = await db.get_channels()
    if not channels:
        list_text = get_text("uz", "no_channels")
    else:
        list_text = "\n".join(f"• {c['title']} (ID: {c['chat_id']})" for c in channels)
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text("uz", "admin_channel_add"), callback_data="adm_ch_add"))
    for c in channels:
        builder.row(InlineKeyboardButton(text=f"➖ {c['title'][:25]}", callback_data=f"adm_ch_del:{c['chat_id']}"))
    builder.row(InlineKeyboardButton(text=get_text("uz", "admin_back"), callback_data="adm_back"))
    await callback.message.edit_text(
        get_text("uz", "admin_channel_list", list=list_text),
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "adm_ch_add")
async def admin_channel_add_prompt(callback: CallbackQuery) -> None:
    if not await _is_admin_db(callback.from_user.id):
        await callback.answer(get_text("uz", "admin_denied"), show_alert=True)
        return
    await callback.answer()
    uid = callback.from_user.id
    _admin_state[uid] = "add_channel"
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text("uz", "admin_back"), callback_data="adm_channels"))
    await callback.message.edit_text(
        get_text("uz", "admin_send_channel"),
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("adm_ch_del:"))
async def admin_channel_remove(callback: CallbackQuery) -> None:
    if not await _is_admin_db(callback.from_user.id):
        await callback.answer(get_text("uz", "admin_denied"), show_alert=True)
        return
    chat_id = int(callback.data.split(":", 1)[1])
    db = get_db()
    await db.remove_channel(chat_id)
    await callback.answer(get_text("uz", "admin_channel_removed"))
    # Refresh list
    channels = await db.get_channels()
    if not channels:
        list_text = get_text("uz", "no_channels")
    else:
        list_text = "\n".join(f"• {c['title']} (ID: {c['chat_id']})" for c in channels)
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text("uz", "admin_channel_add"), callback_data="adm_ch_add"))
    for c in channels:
        builder.row(InlineKeyboardButton(text=f"➖ {c['title'][:25]}", callback_data=f"adm_ch_del:{c['chat_id']}"))
    builder.row(InlineKeyboardButton(text=get_text("uz", "admin_back"), callback_data="adm_back"))
    await callback.message.edit_text(
        get_text("uz", "admin_channel_list", list=list_text),
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )
