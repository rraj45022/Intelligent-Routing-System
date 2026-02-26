from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from backend.core.config import settings

# Naming convention keeps Alembic migrations predictable
naming_convention = {
	"ix": "ix_%(column_0_label)s",
	"uq": "uq_%(table_name)s_%(column_0_name)s",
	"ck": "ck_%(table_name)s_%(constraint_name)s",
	"fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
	"pk": "pk_%(table_name)s",
}
metadata = MetaData(naming_convention=naming_convention)

# Base declarative class used by SQLAlchemy models
Base = declarative_base(metadata=metadata)

# Async engine and session factory
engine = create_async_engine(str(settings.database_url), echo=settings.env == "local", future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
	"""Provide a DB session for FastAPI dependency injection."""
	async with AsyncSessionLocal() as session:
		yield session
