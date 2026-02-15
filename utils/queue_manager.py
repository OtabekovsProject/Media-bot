"""asyncio Queue-based rate limiting: per-user (2) and global (5) parallel tasks."""
import asyncio
from config import USER_PARALLEL_LIMIT, GLOBAL_PARALLEL_LIMIT, REQUEST_DELAY_SEC

# Global semaphore: max 5 concurrent downloads
_global_semaphore: asyncio.Semaphore | None = None
# Per-user: max 2 concurrent tasks per user
_user_semaphores: dict[int, asyncio.Semaphore] = {}
_lock = asyncio.Lock()


def _get_global_semaphore() -> asyncio.Semaphore:
    global _global_semaphore
    if _global_semaphore is None:
        _global_semaphore = asyncio.Semaphore(GLOBAL_PARALLEL_LIMIT)
    return _global_semaphore


def _get_user_semaphore(user_id: int) -> asyncio.Semaphore:
    if user_id not in _user_semaphores:
        _user_semaphores[user_id] = asyncio.Semaphore(USER_PARALLEL_LIMIT)
    return _user_semaphores[user_id]


async def acquire(user_id: int) -> None:
    """Acquire global + user semaphore. Call before starting a download task."""
    await asyncio.sleep(REQUEST_DELAY_SEC)
    await _get_global_semaphore().acquire()
    await _get_user_semaphore(user_id).acquire()


def release(user_id: int) -> None:
    """Release global + user semaphore. Call when task finishes."""
    _get_global_semaphore().release()
    _get_user_semaphore(user_id).release()


class queue_manager:
    """Context manager: acquire on enter, release on exit."""

    def __init__(self, user_id: int):
        self.user_id = user_id

    async def __aenter__(self) -> None:
        await acquire(self.user_id)

    async def __aexit__(self, *args) -> None:
        release(self.user_id)
