"""SQLite database for users and logs (async aiosqlite)."""
import aiosqlite
from pathlib import Path

from config import BASE_DIR

DB_PATH = BASE_DIR / "bot_data.db"


class Database:
    def __init__(self):
        self._connection = None

    async def connect(self) -> None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._connection = await aiosqlite.connect(DB_PATH)
        self._connection.row_factory = aiosqlite.Row
        await self._init_tables()

    async def _init_tables(self) -> None:
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                language TEXT NOT NULL DEFAULT 'uz',
                lang_chosen INTEGER NOT NULL DEFAULT 0,
                first_name TEXT,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        try:
            await self._connection.execute("ALTER TABLE users ADD COLUMN lang_chosen INTEGER NOT NULL DEFAULT 0")
            await self._connection.commit()
        except Exception:
            await self._connection.rollback()
        for col in ("first_name", "username"):
            try:
                await self._connection.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
                await self._connection.commit()
            except Exception:
                await self._connection.rollback()
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                added_by INTEGER NOT NULL
            )
        """)
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL UNIQUE,
                title TEXT NOT NULL,
                username TEXT,
                invite_link TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await self._connection.commit()

    async def get_user_language(self, user_id: int) -> str:
        cursor = await self._connection.execute(
            "SELECT language FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return row["language"] if row else "uz"

    async def set_user_language(self, user_id: int, language: str) -> None:
        await self._connection.execute(
            """
            INSERT INTO users (user_id, language, lang_chosen) VALUES (?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET language = excluded.language, lang_chosen = 1
            """,
            (user_id, language),
        )
        await self._connection.commit()

    async def get_lang_chosen(self, user_id: int) -> bool:
        try:
            cursor = await self._connection.execute(
                "SELECT lang_chosen FROM users WHERE user_id = ?", (user_id,)
            )
            row = await cursor.fetchone()
            if row is None:
                return False
            return bool(row["lang_chosen"])
        except Exception:
            return False

    async def ensure_user(
        self, user_id: int, language: str = "uz", first_name: str | None = None, username: str | None = None
    ) -> None:
        fn = (first_name or "").strip()
        un = (username or "").strip()
        await self._connection.execute(
            """
            INSERT INTO users (user_id, language, lang_chosen, first_name, username)
            VALUES (?, ?, 0, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                first_name = CASE WHEN ? != '' THEN ? ELSE users.first_name END,
                username = CASE WHEN ? != '' THEN ? ELSE users.username END
            """,
            (user_id, language, fn, un, fn, fn, un, un),
        )
        await self._connection.commit()

    async def log_action(self, user_id: int, action: str) -> None:
        await self._connection.execute(
            "INSERT INTO logs (user_id, action) VALUES (?, ?)",
            (user_id, action),
        )
        await self._connection.commit()

    # ----- Admins -----
    async def is_admin(self, user_id: int) -> bool:
        """Faqat DB dagi admins jadvalidan tekshiradi (ADMIN_ID main/admin da tekshiriladi)."""
        cursor = await self._connection.execute(
            "SELECT 1 FROM admins WHERE user_id = ?", (user_id,)
        )
        return (await cursor.fetchone()) is not None

    async def add_admin(self, user_id: int, added_by: int) -> bool:
        await self._connection.execute(
            "INSERT OR IGNORE INTO admins (user_id, added_by) VALUES (?, ?)",
            (user_id, added_by),
        )
        await self._connection.commit()
        return True

    async def remove_admin(self, user_id: int) -> bool:
        await self._connection.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
        await self._connection.commit()
        return True

    async def get_all_admins(self) -> list[tuple[int, str, int]]:
        """(user_id, added_at, added_by)"""
        cursor = await self._connection.execute(
            "SELECT user_id, added_at, added_by FROM admins ORDER BY added_at"
        )
        rows = await cursor.fetchall()
        return [(r["user_id"], r["added_at"] or "", r["added_by"]) for r in rows]

    # ----- Majburiy obuna kanallari -----
    async def add_channel(self, chat_id: int, title: str, username: str | None = None, invite_link: str | None = None) -> bool:
        await self._connection.execute(
            """INSERT OR REPLACE INTO channels (chat_id, title, username, invite_link)
               VALUES (?, ?, ?, ?)""",
            (chat_id, title, username or "", invite_link or ""),
        )
        await self._connection.commit()
        return True

    async def remove_channel(self, chat_id: int) -> bool:
        await self._connection.execute("DELETE FROM channels WHERE chat_id = ?", (chat_id,))
        await self._connection.commit()
        return True

    async def get_channels(self) -> list[dict]:
        cursor = await self._connection.execute(
            "SELECT id, chat_id, title, username, invite_link FROM channels ORDER BY id"
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_user_count(self) -> int:
        cursor = await self._connection.execute("SELECT COUNT(*) FROM users")
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def get_all_user_ids(self) -> list[int]:
        cursor = await self._connection.execute("SELECT user_id FROM users")
        rows = await cursor.fetchall()
        return [r["user_id"] for r in rows]

    async def get_all_users(self) -> list[dict]:
        """Foydalanuvchilar: user_id, first_name, username (admin panel uchun)."""
        cursor = await self._connection.execute(
            "SELECT user_id, first_name, username, created_at FROM users ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()
        return [
            {
                "user_id": r["user_id"],
                "first_name": (r["first_name"] or "").strip() or "—",
                "username": (r["username"] or "").strip() or "—",
            }
            for r in rows
        ]

    async def close(self) -> None:
        if self._connection:
            await self._connection.close()
            self._connection = None


_db: Database | None = None


def get_db() -> Database:
    global _db
    if _db is None:
        _db = Database()
    return _db
