"""Shazam natijasini saqlash – shazam va youtube_mp3 (link → qo'shiqni topish) uchun."""

_shazam_cache: dict[str, dict] = {}


def get_cache_key(user_id: int, track_id: str) -> str:
    return f"{user_id}:{track_id}"


def set_track(user_id: int, track_id: str, track: dict) -> None:
    _shazam_cache[get_cache_key(user_id, track_id)] = track


def get_track(user_id: int, track_id: str) -> dict | None:
    return _shazam_cache.get(get_cache_key(user_id, track_id))
