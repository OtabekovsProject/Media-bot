"""10 variants inline keyboard from YouTube search results."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Callback data length limit in Telegram is 64 bytes. We use video_id (11 chars) for YouTube.
# So we use: var_<video_id> for each variant.


def get_variants_keyboard(video_ids: list[str], titles: list[str]) -> InlineKeyboardMarkup:
    """Build inline with up to 10 buttons. Each: short title -> var_<video_id>."""
    builder = InlineKeyboardBuilder()
    emoji_nums = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    for i, (vid, title) in enumerate(zip(video_ids[:10], titles[:10])):
        if i >= 10:
            break
        label = f"{emoji_nums[i]} {_shorten(title, 35)}"
        builder.row(
            InlineKeyboardButton(text=label, callback_data=f"var_{vid}"),
        )
    return builder.as_markup()


def _shorten(s: str, max_len: int) -> str:
    if len(s) <= max_len:
        return s
    return s[: max_len - 3].rstrip() + "..."
