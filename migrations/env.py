from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.config import settings
from app.db.base import Base
from app import models  # noqa: F401  # важно: импортируем модели для регистрации в Base.metadata

# Alembic Config
config = context.config

# читаем URL из settings (а не из alembic.ini)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Логирование из alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные для autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url_opt = config.get_main_option("sqlalchemy.url")
    assert url_opt is not None, "sqlalchemy.url must be set in Alembic config"

    context.configure(
        url=url_opt,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def _to_sync_url(url: str) -> str:
    if url.startswith("sqlite+aiosqlite"):
        return url.replace("sqlite+aiosqlite", "sqlite", 1)
    if url.startswith("postgresql+asyncpg"):
        return url.replace("postgresql+asyncpg", "postgresql", 1)
    return url


def run_migrations_online() -> None:
    url_opt = config.get_main_option("sqlalchemy.url")
    assert url_opt is not None, "sqlalchemy.url must be set in Alembic config"

    # URL → переводим в sync-вариант
    sync_url = _to_sync_url(url_opt)

    connectable = create_engine(sync_url, poolclass=pool.NullPool, future=True)

    with connectable.connect() as connection:
        opts = {
            "connection": connection,
            "target_metadata": target_metadata,
            "compare_type": True,
        }
        # Для SQLite включаем batch-режим (иначе ALTER TABLE ломается)
        if connection.dialect.name == "sqlite":
            opts["render_as_batch"] = True

        context.configure(**opts)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
