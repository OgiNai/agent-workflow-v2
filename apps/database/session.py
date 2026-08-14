from functools import lru_cache

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from apps.core.settings import get_auth_settings

_engine: AsyncEngine | None = None


def get_database_engine() -> AsyncEngine:
    """Return the application database engine, creating it lazily."""
    global _engine
    database_url = get_auth_settings().database_url.get_secret_value()

    if _engine is None:
        _engine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
        )

    return _engine


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the application session factory."""
    return async_sessionmaker(
        bind=get_database_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_db_session() -> AsyncSession:
    """Provide an application database session."""
    async with get_session_factory()() as session:
        yield session


async def check_database_connection() -> None:
    """Verify that the database is reachable."""
    engine = get_database_engine()

    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))


async def close_database_engine() -> None:
    """Dispose of the database engine and reset its cached state."""
    global _engine

    if _engine is not None:
        await _engine.dispose()
        _engine = None

    get_session_factory.cache_clear()
