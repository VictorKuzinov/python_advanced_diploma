# app/main.py
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from app.routes import media_router, setup_exception_handlers, tweet_router, user_router


def create_app() -> FastAPI:
    media_dir = Path(__file__).resolve().parent / "media"
    dist_dir = Path(__file__).resolve().parent.parent / "dist"

    app = FastAPI(title="Twitter Clone API", version="1.0.0")
    setup_exception_handlers(app)

    # API
    app.include_router(user_router)
    app.include_router(tweet_router)
    app.include_router(media_router)

    # статика фронта
    app.mount("/css", StaticFiles(directory=dist_dir / "css"), name="css")
    app.mount("/js", StaticFiles(directory=dist_dir / "js"), name="js")
    app.mount("/media", StaticFiles(directory=media_dir), name="media")

    # favicon (если есть)
    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        return FileResponse(dist_dir / "favicon.ico")

    # корневой index.html
    @app.get("/", include_in_schema=False)
    async def index():
        return FileResponse(dist_dir / "index.html")

    # SPA-fallback
    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        if full_path.startswith(("api", "media", "css", "js", "favicon.ico")):
            return PlainTextResponse("Not Found", status_code=404)
        return FileResponse(dist_dir / "index.html")

    return app


# экземпляр для uvicorn
app = create_app()
