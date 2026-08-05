from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from apps.core.settings import get_auth_settings

_engine: AsyncEngine | None = None


def get_database_engine() -> AsyncEngine:
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
    return async_sessionmaker(
        bind=get_database_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_db_session() -> AsyncSession:
    async with get_session_factory()() as session:
        yield session


async def close_database_engine() -> None:
    global _engine

    if _engine is not None:
        await _engine.dispose()
        _engine = None
