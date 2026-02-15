"""Extract URLs from Telegram message (text, caption, entities)."""
import re
from aiogram.types import Message

# YouTube video ID (11 chars): watch, shorts, youtu.be, embed
YT_ID_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.|m\.)?(?:youtube\.com/(?:watch\?v=|shorts/|embed/)|youtu\.be/)([a-zA-Z0-9_-]{11})"
)
# Any http(s) URL
URL_PATTERN = re.compile(r"https?://[^\s\]\[\)]+", re.IGNORECASE)


def get_text_for_urls(message: Message) -> str:
    """Get string to search for URLs: text or caption."""
    if message.text:
        return message.text
    if message.caption:
        return message.caption
    return ""


def extract_youtube_id(text: str) -> str | None:
    """Extract first YouTube video ID from text. Returns None if not found."""
    if not text:
        return None
    m = YT_ID_PATTERN.search(text)
    return m.group(1) if m else None


def extract_first_url(text: str) -> str | None:
    """Extract first http(s) URL from text."""
    if not text:
        return None
    m = URL_PATTERN.search(text)
    return m.group(0).rstrip(".,;:)") if m else None


def get_youtube_id_from_message(message: Message) -> str | None:
    """Get YouTube video ID from message (text, caption, or entities)."""
    text = get_text_for_urls(message)
    vid = extract_youtube_id(text)
    if vid:
        return vid
    if message.entities and text:
        for ent in message.entities:
            if ent.type == "url":
                start, end = ent.offset, ent.offset + ent.length
                url = text[start:end]
                vid = extract_youtube_id(url)
                if vid:
                    return vid
            if ent.type == "text_link" and ent.url:
                vid = extract_youtube_id(ent.url)
                if vid:
                    return vid
    return None


def get_first_url_from_message(message: Message) -> str | None:
    """Get first URL from message (text, caption, or entities)."""
    text = get_text_for_urls(message)
    url = extract_first_url(text)
    if url:
        return url
    if message.entities and text:
        for ent in message.entities:
            if ent.type == "text_link" and ent.url:
                return ent.url
            if ent.type == "url":
                start, end = ent.offset, ent.offset + ent.length
                return text[start:end]
    return None
