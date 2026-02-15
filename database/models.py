"""Database models: users and logs (sync)."""
from .db import get_db, close_db


def ensure_user(user_id: int, language: str = "uz") -> None:
    """Create user if not exist."""
    conn = get_db()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO users (user_id, language) VALUES (?, ?)",
            (user_id, language),
        )
        conn.commit()
    finally:
        close_db(conn)


def get_user_language(user_id: int) -> str:
    """Get user language; default 'uz'."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT language FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        return row["language"] if row else "uz"
    finally:
        close_db(conn)


def set_user_language(user_id: int, language: str) -> None:
    """Set user language."""
    ensure_user(user_id, language)
    conn = get_db()
    try:
        conn.execute(
            "UPDATE users SET language = ? WHERE user_id = ?",
            (language, user_id),
        )
        conn.commit()
    finally:
        close_db(conn)


def log_action(user_id: int, action: str) -> None:
    """Log user action."""
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO logs (user_id, action) VALUES (?, ?)",
            (user_id, action),
        )
        conn.commit()
    finally:
        close_db(conn)
