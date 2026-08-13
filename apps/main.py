"""FastAPI application entry point."""

import logging.config
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from apps.api.feedback import router as feedback_router
from apps.api.health import router as health_router
from apps.api.reviews import router as reviews_router
from apps.core.config import LOGGING_CONFIG
from apps.core.settings import get_auth_settings
from apps.database.session import close_database_engine
from apps.llm.gemini_client import close_gemini_client

logging.config.dictConfig(LOGGING_CONFIG)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # TODO Future startup operations:
    # - verify configuration
    # - initialize database connection pool
    # - initialize telemetry
    try:
        # call get_auth_settings to make sure that if
        get_auth_settings()
        yield
    finally:
        await close_gemini_client()
        await close_database_engine()
        # TODO await shutdown_telemetry()


code_app = FastAPI(
    title="AI Code Review and Refactoring Platform",
    version="0.2.0",
    lifespan=lifespan,
)

code_app.include_router(health_router)
code_app.include_router(reviews_router, tags=["reviews"])
code_app.include_router(feedback_router, tags=["feedback"])
