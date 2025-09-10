# app/routes/__init__.py
from .exception_handlers import setup_exception_handlers
from .dependencies import get_current_user
from .user import router as user_router
from .tweet import router as tweet_router
from .media import router as media_router

__all__ = [
    "setup_exception_handlers",
    "get_current_user",
    "user_router",
    "tweet_router",
    "media_router",
]