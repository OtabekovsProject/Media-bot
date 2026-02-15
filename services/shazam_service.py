"""Shazam recognition via Shazamio. Tries multiple segments (middle, start, end, full) for best result."""
import asyncio
from pathlib import Path
from shazamio import Shazam

from config import TEMP_DIR

SEGMENT_SEC = 20.0
MIN_LENGTH_MS = 4000


def _extract_segment(input_path: Path, start_ratio: float, end_ratio: float, suffix: str) -> Path | None:
    """Extract part of audio: start_ratio..end_ratio (0=start, 1=end). Returns temp path or None."""
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(str(input_path))
        total_ms = len(audio)
        if total_ms < MIN_LENGTH_MS:
            return None
        start_ms = int(total_ms * start_ratio)
        end_ms = int(total_ms * end_ratio)
        want_ms = int(SEGMENT_SEC * 1000)
        if end_ms - start_ms < MIN_LENGTH_MS:
            return None
        segment = audio[start_ms:min(start_ms + want_ms, end_ms)]
        out = TEMP_DIR / f"shazam_seg_{input_path.stem}_{suffix}.mp3"
        segment.export(str(out), format="mp3", bitrate="192k")
        return out if out.exists() else None
    except Exception:
        return None


def _extract_middle_segment(input_path: Path, segment_sec: float = 22.0) -> Path | None:
    """Middle part – Shorts/Reels uchun yaxshi."""
    return _extract_segment(input_path, 0.4, 0.6, "mid")


def _extract_start_segment(input_path: Path) -> Path | None:
    return _extract_segment(input_path, 0.0, 0.4, "start")


def _extract_end_segment(input_path: Path) -> Path | None:
    return _extract_segment(input_path, 0.6, 1.0, "end")


def _extract_first_sec(input_path: Path, max_sec: float = 45.0) -> Path | None:
    """Birinchi max_sec soniya – tezroq tanlash uchun."""
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(str(input_path))
        total_ms = len(audio)
        if total_ms < MIN_LENGTH_MS:
            return None
        want_ms = min(int(max_sec * 1000), total_ms)
        segment = audio[:want_ms]
        out = TEMP_DIR / f"shazam_seg_{input_path.stem}_first.mp3"
        segment.export(str(out), format="mp3", bitrate="192k")
        return out if out.exists() else None
    except Exception:
        return None


class ShazamService:
    def __init__(self):
        self._shazam = Shazam()

    async def _recognize_path(self, path: Path) -> dict | None:
        try:
            result = await self._shazam.recognize(str(path))
            if not result or "track" not in result:
                return None
            track = result["track"]
            return {
                "key": track.get("key"),
                "title": track.get("title", "Unknown"),
                "subtitle": track.get("subtitle", "Unknown"),
                "sections": track.get("sections"),
                "url": track.get("url"),
                "images": track.get("images"),
            }
        except Exception:
            return None

    async def recognize_file(self, audio_path: Path, use_middle_segment: bool = False) -> dict | None:
        """Recognize from file. use_middle_segment=True: faqat o'rta segment."""
        path = audio_path
        segment_path = None
        if use_middle_segment:
            segment_path = _extract_middle_segment(audio_path, 22.0)
            if segment_path:
                path = segment_path
        try:
            out = await self._recognize_path(path)
            return out
        finally:
            if segment_path and segment_path.exists():
                try:
                    segment_path.unlink(missing_ok=True)
                except Exception:
                    pass

    async def recognize_file_thorough(self, audio_path: Path) -> dict | None:
        """Bir nechta segmentda qidirish: to'liq → o'rta → bosh → oxir → birinchi 45s. Haqiqatan topilmasa None."""
        # 1) To'liq fayl (qisqa bo'lsa tez)
        if audio_path.exists() and audio_path.stat().st_size > 0:
            track = await self._recognize_path(audio_path)
            if track:
                return track
        # 2) Segmentlar
        segments_to_try = [
            lambda: _extract_middle_segment(audio_path, SEGMENT_SEC),
            lambda: _extract_start_segment(audio_path),
            lambda: _extract_end_segment(audio_path),
            lambda: _extract_first_sec(audio_path, 45.0),
        ]
        for get_seg in segments_to_try:
            seg = get_seg()
            if not seg or not seg.exists():
                continue
            try:
                track = await self._recognize_path(seg)
                if track:
                    return track
            finally:
                if seg.exists():
                    try:
                        seg.unlink(missing_ok=True)
                    except Exception:
                        pass
        return None
