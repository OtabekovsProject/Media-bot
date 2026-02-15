"""Shazam result inline keyboard: YouTube, 10 variants, Details."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.i18n import get_text


def get_shazam_result_keyboard(
    query: str,
    song_id: str,
    lang: str = "uz",
) -> InlineKeyboardMarkup:
    """Three buttons: YouTube download, 10 variants, Details.
    query: search query (artist - title).
    song_id: optional id for details (we pass query for YouTube search).
    """
    builder = InlineKeyboardBuilder()
    download_label = get_text(lang, "btn_youtube")
    variants_label = get_text(lang, "btn_10_variants")
    details_label = get_text(lang, "btn_details")
    # Telegram callback_data max 64 bytes (prefixes yt_one: variants: details:)
    def truncate(s: str, max_bytes: int) -> str:
        b = s.encode("utf-8")[:max_bytes]
        return b.decode("utf-8", errors="ignore")
    q = truncate(query, 56)
    sid = truncate(song_id or query, 55)
    builder.row(
        InlineKeyboardButton(text=download_label, callback_data=f"yt_one:{q}"),
    )
    builder.row(
        InlineKeyboardButton(text=variants_label, callback_data=f"variants:{q}"),
    )
    builder.row(
        InlineKeyboardButton(text=details_label, callback_data=f"details:{sid}"),
    )
    return builder.as_markup()
