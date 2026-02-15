"""Internal protection: asyncio queue, per-user and global limits."""
import asyncio
from collections import defaultdict
from typing import Callable, Any

from config import (
    USER_PARALLEL_LIMIT,
    GLOBAL_PARALLEL_LIMIT,
    REQUEST_DELAY_SEC,
)

# Per-user semaphore: max 2 tasks per user
_user_sem: dict[int, asyncio.Semaphore] = {}
_user_lock = asyncio.Lock()

# Global semaphore: max 5 parallel downloads
_global_sem = asyncio.Semaphore(GLOBAL_PARALLEL_LIMIT)


def _get_user_sem(user_id: int) -> asyncio.Semaphore:
    if user_id not in _user_sem:
        _user_sem[user_id] = asyncio.Semaphore(USER_PARALLEL_LIMIT)
    return _user_sem[user_id]


async def run_with_limits(user_id: int, coro_factory: Callable[[], Any]) -> Any:
    """
    Run a coroutine with:
    - 1 slot from global semaphore (max 5 total)
    - 1 slot from user semaphore (max 2 per user)
    - 0.5s delay before starting (internal, invisible to user)
    """
    await asyncio.sleep(REQUEST_DELAY_SEC)
    async with _global_sem:
        async with _get_user_sem(user_id):
            coro = coro_factory() if callable(coro_factory) else coro_factory
            return await coro


class task_queue:
    """Namespace for queue helpers."""

    @staticmethod
    async def run(user_id: int, coro_factory: Callable[[], Any]) -> Any:
        return await run_with_limits(user_id, coro_factory)
