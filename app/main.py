from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import media_router, setup_exception_handlers, tweet_router, user_router

media_dir = Path(__file__).resolve().parent / "media"


def create_app() -> FastAPI:
    app = FastAPI(
        title="Twitter Clone API",
        version="1.0.0",
    )

    # глобальные обработчики ошибок
    setup_exception_handlers(app)

    # здесь будут роуты
    app.include_router(user_router)
    app.include_router(tweet_router)
    app.include_router(media_router)

    return app


app = create_app()

app.mount("/media", StaticFiles(directory=media_dir), name="media")
