# app/tests/conftest.py
import asyncio
import os
import tempfile
from typing import AsyncGenerator, Generator

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.base import Base
from app.db.session import get_session
from app.main import create_app
from app.models import Follow, Like, Tweet, User


# ---------- синхронные фикстуры ----------
@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Собственный event loop на сессию (для pytest-asyncio strict)."""
    loop = asyncio.new_event_loop()
    try:
        yield loop
    finally:
        loop.close()


@pytest.fixture(scope="session")
def tmp_db_file() -> Generator[str, None, None]:
    """Временный файл SQLite для тестовой БД."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        yield path
    finally:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass


@pytest.fixture(scope="session")
def test_database_url(tmp_db_file: str) -> str:
    """URL aiosqlite к временному файлу."""
    return f"sqlite+aiosqlite:///{tmp_db_file}"


# ---------- асинхронные фикстуры ----------
@pytest_asyncio.fixture(scope="session")
async def engine(test_database_url: str) -> AsyncGenerator[AsyncEngine, None]:
    """Создаём async-движок, поднимаем схему, по окончании — дропаем."""
    eng: AsyncEngine = create_async_engine(test_database_url, future=True, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield eng
    finally:
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await eng.dispose()


@pytest.fixture(scope="session")
def SessionLocal(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Фабрика async-сессий."""
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture
async def session(
    SessionLocal: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """Живой AsyncSession на время теста."""
    async with SessionLocal() as s:
        yield s


@pytest_asyncio.fixture
async def app_overridden(session: AsyncSession) -> FastAPI:
    """FastAPI-приложение с переопределённой зависимостью get_session."""
    app = create_app()

    async def _override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield session

    app.dependency_overrides[get_session] = _override_get_session
    return app


@pytest_asyncio.fixture
async def client(app_overridden: FastAPI) -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTP-клиент на ASGI-транспорте (без сети)."""
    transport = httpx.ASGITransport(app=app_overridden)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def seed_users(session: AsyncSession) -> dict[str, dict[str, int | str]]:
    """Чистим БД и добавляем трёх пользователей."""
    # Чистка (важен порядок FK)
    await session.execute(delete(Like))
    await session.execute(delete(Follow))
    await session.execute(delete(Tweet))
    await session.execute(delete(User))
    await session.commit()

    users = [
        User(username="alice", api_key="alice-key-123"),
        User(username="bob", api_key="bob-key-456"),
        User(username="jack", api_key="jack-key-789"),
    ]
    session.add_all(users)
    await session.commit()
    # вернуть удобный словарь
    return {
        "alice": {"id": users[0].id, "api_key": users[0].api_key},
        "bob": {"id": users[1].id, "api_key": users[1].api_key},
        "jack": {"id": users[2].id, "api_key": users[2].api_key},
    }
