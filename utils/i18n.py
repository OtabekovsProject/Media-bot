"""Simple i18n: language -> key -> text."""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
LOCALES = BASE / "locales"

TEXTS = {
    "uz": {
        "welcome": "👋 Assalomu alaykum! Tilni tanlang:",
        "lang_set": "✅ Til o'rnatildi: O'zbek",
        "send_audio": "🎵 Qo'shiqni aniqlash uchun audio, video yoki ovozli xabar yuboring.",
        "shazam_found": "🎵 <b>Qo'shiq topildi</b>\n\n<b>Nomi:</b> {title}\n<b>Ijrochi:</b> {artist}\n<b>Albom:</b> {album}\n<b>Janr:</b> {genre}\n<b>Yil:</b> {year}",
        "shazam_not_found": "❌ Qo'shiq aniqlanmadi. Boshqa audio yuboring.",
        "shazam_error": "⚠️ Audio qayta ishlanmoqda. Keyinroq urinib ko'ring.",
        "btn_youtube": "🎵 YouTube'dan yuklab olish",
        "btn_10_variants": "📀 10 ta variant",
        "btn_details": "🔍 Batafsil",
        "send_yt_link": "🔗 YouTube linkini yuboring yoki Shazam natijasidan tanlang.",
        "loading": "⏳ Yuklanmoqda...",
        "ready_mp3": "✅ MP3 tayyor!",
        "mp3_caption": "🎵 {title}\n👤 {artist}\n💿 {album}\n⏱ {duration}",
        "send_link": "📎 Instagram, YouTube, TikTok yoki Pinterest linkini yuboring.",
        "platform_ok": "✅ Yuklab olinmoqda...",
        "error_download": "❌ Yuklab olish amalga oshmadi.",
        "error_size": "❌ Fayl hajmi chegaradan oshdi.",
        "error_generic": "⚠️ Xatolik yuz berdi. Keyinroq urinib ko'ring.",
        "choose_variant": "📀 Quyidagilardan birini tanlang:",
        "unknown": "Noma'lum",
        "year_unknown": "—",
        "hint": "📎 Instagram, YouTube, TikTok yoki Pinterest linkini yuboring.\n🎵 Yoki qo'shiqni aniqlash uchun audio, video yoki ovozli xabar yuboring.",
    },
    "ru": {
        "welcome": "👋 Здравствуйте! Выберите язык:",
        "lang_set": "✅ Язык установлен: Русский",
        "send_audio": "🎵 Отправьте аудио, видео или голосовое сообщение для распознавания.",
        "shazam_found": "🎵 <b>Трек найден</b>\n\n<b>Название:</b> {title}\n<b>Исполнитель:</b> {artist}\n<b>Альбом:</b> {album}\n<b>Жанр:</b> {genre}\n<b>Год:</b> {year}",
        "shazam_not_found": "❌ Трек не распознан. Отправьте другое аудио.",
        "shazam_error": "⚠️ Обработка аудио. Попробуйте позже.",
        "btn_youtube": "🎵 Скачать с YouTube",
        "btn_10_variants": "📀 10 вариантов",
        "btn_details": "🔍 Подробнее",
        "send_yt_link": "🔗 Отправьте ссылку YouTube или выберите из результатов Shazam.",
        "loading": "⏳ Загрузка...",
        "ready_mp3": "✅ MP3 готов!",
        "mp3_caption": "🎵 {title}\n👤 {artist}\n💿 {album}\n⏱ {duration}",
        "send_link": "📎 Отправьте ссылку Instagram, YouTube, TikTok или Pinterest.",
        "platform_ok": "✅ Загружаем...",
        "error_download": "❌ Не удалось загрузить.",
        "error_size": "❌ Размер файла превышает лимит.",
        "error_generic": "⚠️ Произошла ошибка. Попробуйте позже.",
        "choose_variant": "📀 Выберите вариант:",
        "unknown": "Неизвестно",
        "year_unknown": "—",
        "hint": "📎 Отправьте ссылку Instagram, YouTube, TikTok или Pinterest.\n🎵 Или отправьте аудио, видео или голосовое сообщение для распознавания.",
    },
    "en": {
        "welcome": "👋 Hello! Choose language:",
        "lang_set": "✅ Language set: English",
        "send_audio": "🎵 Send audio, video or voice message to recognize the track.",
        "shazam_found": "🎵 <b>Track found</b>\n\n<b>Title:</b> {title}\n<b>Artist:</b> {artist}\n<b>Album:</b> {album}\n<b>Genre:</b> {genre}\n<b>Year:</b> {year}",
        "shazam_not_found": "❌ Track not recognized. Send another audio.",
        "shazam_error": "⚠️ Processing audio. Try again later.",
        "btn_youtube": "🎵 Download from YouTube",
        "btn_10_variants": "📀 10 variants",
        "btn_details": "🔍 Details",
        "send_yt_link": "🔗 Send a YouTube link or choose from Shazam results.",
        "loading": "⏳ Loading...",
        "ready_mp3": "✅ MP3 ready!",
        "mp3_caption": "🎵 {title}\n👤 {artist}\n💿 {album}\n⏱ {duration}",
        "send_link": "📎 Send Instagram, YouTube, TikTok or Pinterest link.",
        "platform_ok": "✅ Downloading...",
        "error_download": "❌ Download failed.",
        "error_size": "❌ File size exceeds limit.",
        "error_generic": "⚠️ Something went wrong. Try again later.",
        "choose_variant": "📀 Choose one:",
        "unknown": "Unknown",
        "year_unknown": "—",
        "hint": "📎 Send Instagram, YouTube, TikTok or Pinterest link.\n🎵 Or send audio, video or voice message to recognize a track.",
    },
}


def get_text(lang: str, key: str, **kwargs) -> str:
    """Get localized text. Fallback to 'en' then raw key."""
    text = TEXTS.get(lang, TEXTS["en"]).get(key, TEXTS["en"].get(key, key))
    return text.format(**kwargs) if kwargs else text
