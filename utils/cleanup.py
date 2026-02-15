"""Clean temporary files after use."""
from pathlib import Path

from config import TEMP_DIR


def cleanup_temp_file(path: Path | str | None) -> None:
    """Delete a single file if it exists. Safe to call with None."""
    if path is None:
        return
    p = Path(path)
    if p.exists() and p.is_file():
        try:
            p.unlink()
        except OSError:
            pass


def cleanup_user_temp(user_id: int) -> None:
    """Remove temporary files for user (call after sending file)."""
    try:
        ud = TEMP_DIR / str(user_id)
        if ud.exists():
            for f in ud.iterdir():
                try:
                    f.unlink()
                except OSError:
                    pass
            try:
                ud.rmdir()
            except OSError:
                pass
    except Exception:
        pass
