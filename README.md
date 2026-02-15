# 🎵 Professional Telegram Media Bot

Shazam, YouTube 🎧Audio, **Instagram / TikTok / Facebook / Pinterest** dan to‘liq video va 🎧Audio yuklash; videodagi musiqani aniqlash (Qo‘shiqni to‘liq topish). 10 ta variant inline.

## Texnologiyalar

- Python 3.11
- aiogram 3.x
- yt-dlp (barcha platformalar)
- Shazamio (videodan musiqa aniqlash)
- FFmpeg (Docker/Render da o‘rnatiladi)
- SQLite (aiosqlite), asyncio queue

## Render ga deploy

1. [Render](https://render.com) da **New → Web Service**.
2. Repo ulang yoki **Docker** tanlang; **Dockerfile path:** `bot/Dockerfile`, **Root directory:** `bot` (yoki loyiha ildizi `bot` bo‘lsa – shu).
3. **Environment:** `BOT_TOKEN`, `ADMIN_ID` (Render Secret Files yoki Environment Variables).
4. **Deploy.** Render avtomatik `PORT` beradi; bot health server shu portda ishlaydi, uxlamaydi.

Yoki **Blueprint** bilan: `render.yaml` ni repo ga qo‘shing → Render Dashboard da **New → Blueprint** → reponi tanlang.

## Oʻrnatish (lokal)

```bash
cd bot
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

**FFmpeg:** `requirements.txt` dagi **imageio-ffmpeg** orqali pip bilan avtomatik o‘rnatiladi (🎧Audio/Video uchun). Agar tizimda FFmpeg allaqachon bo‘lsa yoki `install_ffmpeg.bat` ni ishlatgan bo‘lsangiz, bot uni avtomatik topadi.

`.env` yarating (`.env.example` dan nusxa oling):

```
BOT_TOKEN=your_bot_token
ADMIN_ID=your_telegram_user_id
MAX_FILE_SIZE_MB=50
```

## Ishga tushirish

```bash
python main.py
```

## Funksiyalar

- **/start** — til tanlash (O‘zbek, Русский, English).
- **Shazam** — audio, video yoki ovoz yuboring → qo‘shiq aniqlanadi → YouTube / 10 variant / Batafsil.
- **YouTube link** → 🎧Audio, Video yoki **Qo‘shiqni to‘liq topish** (videodan musiqa).
- **Instagram / TikTok / Facebook / Pinterest link** → **Video**, **🎧Audio** yoki **Qo‘shiqni to‘liq topish** (videodagi musiqani Shazam orqali topadi). To‘liq va aniq yuklash, platformaga xos sozlamalar.
- **10 ta variant** — Shazam natijasidan “10 ta variant” → tanlangan trek 🎧Audio.

## Ichki himoya (foydalanuvchi ko‘rmaydi)

- `asyncio.Queue`: 1 user uchun 2 parallel task, global 5 parallel.
- Har bir so‘rov oldin 0.5 s delay.
- MAX_FILE_SIZE (default 50 MB).
- Vaqtinchalik fayllar yuborilgach o‘chiriladi.

## Kataloglar

```
bot/
├── main.py
├── config.py
├── handlers/
├── services/
├── database/
├── keyboards/
└── utils/
```
