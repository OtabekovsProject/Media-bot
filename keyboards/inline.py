"""Inline keyboards."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

LANG_CALLBACK_PREFIX = "lang:"
VARIANT_CALLBACK_PREFIX = "var:"
SHAZAM_YT_PREFIX = "shazam_yt:"
SHAZAM_VARIANTS_PREFIX = "shazam_var:"
SHAZAM_DETAILS_PREFIX = "shazam_det:"


def get_language_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang:uz"),
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
        InlineKeyboardButton(text="🇺🇸 English", callback_data="lang:en"),
    )
    return builder.as_markup()


def build_shazam_result_keyboard(track_id: str, lang: str = "uz") -> InlineKeyboardMarkup:
    """Keyboard after Shazam: YouTube download, 10 variants, Details."""
    from utils.locales import get_text
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_text(lang, "download_yt"),
            callback_data=f"{SHAZAM_YT_PREFIX}{track_id}",
        ),
        InlineKeyboardButton(
            text=get_text(lang, "ten_variants"),
            callback_data=f"{SHAZAM_VARIANTS_PREFIX}{track_id}",
        ),
        InlineKeyboardButton(
            text=get_text(lang, "details"),
            callback_data=f"{SHAZAM_DETAILS_PREFIX}{track_id}",
        ),
    )
    return builder.as_markup()


def build_variants_keyboard(variants: list[dict], query: str) -> InlineKeyboardMarkup:
    """10 variants: each button = video_id, label = short title."""
    builder = InlineKeyboardBuilder()
    emoji_nums = "1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣8️⃣9️⃣🔟"
    for i, v in enumerate(variants[:10]):
        title = v.get("title", "Track")[:40]
        vid = v.get("id") or v.get("video_id", "")
        if vid:
            builder.row(
                InlineKeyboardButton(
                    text=f"{emoji_nums[i]} {title}",
                    callback_data=f"{VARIANT_CALLBACK_PREFIX}{vid}",
                )
            )
    return builder.as_markup()
