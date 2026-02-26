import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from backend.core.config import settings
from backend.core.db import Base

# Import models so Alembic sees table metadata
from backend.models import associate, tickets, user  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Alembic gets the URL from application settings
config.set_main_option("sqlalchemy.url", str(settings.database_url))

target_metadata = Base.metadata


def _sync_url() -> str:
    """Convert async driver URL to sync variant for offline mode."""
    url = config.get_main_option("sqlalchemy.url")
    return url.replace("+asyncpg", "") if url else ""


def run_migrations_offline() -> None:
    context.configure(
        url=_sync_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async def process_migrations() -> None:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
        await connectable.dispose()

    asyncio.run(process_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
