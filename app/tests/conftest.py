# app/tests/conftest.py
import asyncio
import os
import tempfile
from typing import AsyncGenerator

import pytest_asyncio
import httpx
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import create_app
from app.db.base import Base
from app.db.session import get_session
from app.models import User, Like, Follow, Tweet

@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
def tmp_db_file():
    # отдельная БД для тестов
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    try:
        os.remove(path)
    except FileNotFoundError:
        pass

@pytest_asyncio.fixture(scope="session")
def test_database_url(tmp_db_file) -> str:
    return f"sqlite+aiosqlite:///{tmp_db_file}"

@pytest_asyncio.fixture(scope="session")
async def engine(test_database_url: str):
    eng = create_async_engine(test_database_url, future=True)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()

@pytest_asyncio.fixture(scope="session")
def SessionLocal(engine):
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

@pytest_asyncio.fixture
async def session(SessionLocal) -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as s:
        yield s

@pytest_asyncio.fixture
async def app_overridden(session):
    app = create_app()

    async def _override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield session

    app.dependency_overrides[get_session] = _override_get_session
    return app

@pytest_asyncio.fixture
async def client(app_overridden):
    transport = httpx.ASGITransport(app=app_overridden)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture
async def seed_users(session: AsyncSession):
    # Чистим БД (важен порядок FK)
    await session.execute(delete(Like))
    await session.execute(delete(Follow))
    await session.execute(delete(Tweet))
    await session.execute(delete(User))
    await session.commit()
    # создаём 3 тестовых пользователя
    users = [
        User(username="alice", api_key="alice-key-123"),
        User(username="bob",   api_key="bob-key-456"),
        User(username="jack",  api_key="jack-key-789"),
    ]
    session.add_all(users)
    await session.commit()
    # вернём словарь api-key → id/username
    return {
        "alice": {"id": users[0].id, "api_key": users[0].api_key},
        "bob":   {"id": users[1].id, "api_key": users[1].api_key},
        "jack":  {"id": users[2].id, "api_key": users[2].api_key},
    }
