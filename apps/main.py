"""FastAPI application entry point."""

import logging.config

from fastapi import FastAPI

from apps.api.feedback import router as feedback_router
from apps.api.health import router as health_router
from apps.api.legacy_code import router as legacy_code_router
from apps.api.reviews import router as reviews_router
from apps.config import LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)

code_app = FastAPI(
    title="Agentic Code Review Platform",
    version="0.2.0",
)

code_app.include_router(health_router)
code_app.include_router(reviews_router, tags=["reviews"])
code_app.include_router(feedback_router, tags=["feedback"])
code_app.include_router(legacy_code_router, prefix="/code", tags=["legacy-code"])
