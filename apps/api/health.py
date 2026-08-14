"""Health/readiness endpoints."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from apps.core.settings import get_auth_settings
from apps.database.session import check_database_connection

router = APIRouter(tags=["system"])


@router.get("/health")
async def health():
    """Return a basic liveness response."""
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> JSONResponse:
    """Check whether the application is ready to serve requests."""
    try:
        await check_readiness()
    except ValidationError:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "checks": {
                    "config": "incomplete",
                    "database": "not_checked",
                },
            },
        )
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "checks": {
                    "config": "ok",
                    "database": "unavailable",
                },
            },
        )

    return JSONResponse(
        status_code=200,
        content={
            "status": "ready",
            "checks": {
                "config": "ok",
                "database": "ok",
            },
        },
    )


async def check_readiness() -> None:
    get_auth_settings()
    await check_database_connection()
