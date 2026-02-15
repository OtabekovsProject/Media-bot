from .start import router as start_router
from .language import router as language_router
from .search import router as search_router
from .shazam import router as shazam_router
from .youtube_mp3 import router as youtube_mp3_router
from .media import router as media_router
from .variants import router as variants_router
from .admin import router as admin_router

__all__ = [
    "start_router",
    "language_router",
    "search_router",
    "shazam_router",
    "youtube_mp3_router",
    "media_router",
    "variants_router",
    "admin_router",
]
