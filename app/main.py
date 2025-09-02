from fastapi import FastAPI

from app.routes import setup_exception_handlers
# роутеры подключим позже: from app.routes import users, tweets, media


def create_app() -> FastAPI:
    app = FastAPI(
        title="Twitter Clone API",
        version="1.0.0",
    )

    # глобальные обработчики ошибок
    setup_exception_handlers(app)

    # здесь будут app.include_router(users.router)
    # здесь будут app.include_router(tweets.router)
    # здесь будут app.include_router(media.router)

    return app


app = create_app()