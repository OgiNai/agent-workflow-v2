"""FastAPI application entry point."""

import logging.config
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from apps.api.feedback import router as feedback_router
from apps.api.health import check_readiness
from apps.api.health import router as health_router
from apps.api.reviews import router as reviews_router
from apps.core.logging_config import LOGGING_CONFIG
from apps.database.session import close_database_engine
from apps.llm.gemini_client import close_gemini_client
from apps.observability.telemetry import (
    initialize_telemetry,
    shutdown_telemetry,
)

logging.config.dictConfig(LOGGING_CONFIG)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Lifespan startup happens before the application begins serving requests
    and shutdown happens while the server is done serving requests and is shutting down,
    so synchronous functions called from async lifespan do not block incoming requests"""
    try:
        initialize_telemetry()
        await check_readiness()
        yield
    finally:
        await close_gemini_client()
        await close_database_engine()
        shutdown_telemetry()


code_app = FastAPI(
    title="AI Code Review and Refactoring Platform",
    version="0.2.0",
    lifespan=lifespan,
)

code_app.include_router(health_router)
code_app.include_router(reviews_router, tags=["reviews"])
code_app.include_router(feedback_router, tags=["feedback"])
