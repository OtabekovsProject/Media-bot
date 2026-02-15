"""Audio fayl uchun toza nom: faqat musiqaning nomi (harflar, probel, defis)."""
import re
import unicodedata

MAX_FILENAME_LEN = 120


def sanitize_audio_filename(title: str, artist: str = "") -> str:
    """
    Faqat musiqaning nomi: harflar, probel, defis. Raqamlar va boshqa belgilar olib tashlanadi.
    Natija: "Artist - Title.mp3" yoki "Title.mp3"
    """
    def clean(s: str) -> str:
        if not s or not s.strip():
            return ""
        # Faqat harflar (barcha tillar), probel, defis qoldiramiz
        s = "".join(
            c for c in s
            if unicodedata.category(c).startswith("L") or c in " -"
        )
        # Ortiqcha probellarni bitta qilish
        s = re.sub(r"\s+", " ", s).strip()
        return s[:MAX_FILENAME_LEN]

    t = clean(title or "")
    a = clean(artist or "")
    if a and t:
        name = f"{a} - {t}"
    else:
        name = t or a or "Track"
    # Telegram va fayl tizimi uchun xavfsiz
    name = re.sub(r'[<>:"/\\|?*]', "", name).strip() or "Track"
    return f"{name[:MAX_FILENAME_LEN]}.mp3"
