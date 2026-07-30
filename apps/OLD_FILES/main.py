import logging.config

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from apps.code_endpoints import router as code_router
from apps.config import LOGGING_CONFIG
from apps.core.settings import get_auth_settings

logging.config.dictConfig(LOGGING_CONFIG)

code_app = FastAPI(
    title="Agentic Test 1",
    version="0.1.0",
)

code_app.include_router(
    code_router,
    prefix="/code",
    tags=["code"],
)

@code_app.get("/health", tags=["system"])
async def health():
    """
    Liveness check: Confirms the FastAPI process is running.
    """
    return {"status": "ok"}

@code_app.get("/ready", tags=["system"])
async def ready(agentic_sys: str):
    """
    Readiness check: Confirms the app has the minimum required configuration.

    Args:
        agentic_sys: the agentic system to check readiness for:
            "review" for agent with tools
            "generate" for two-agent system
    """
    try:
        settings = get_auth_settings()

        missing = []

        if not settings.api_token.get_secret_value():
            missing.append("API_TOKEN")

        if not settings.gemini_api_key.get_secret_value():
            missing.append("GEMINI_API_KEY")

        if agentic_sys == "review" and not settings.project_path:
            missing.append("PROJECT_PATH")

        if missing:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "missing": missing,
                },
            )

        return {
            "status": "ready",
            "checks": {
                "config": "ok",
            },
        }

    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "reason": str(e),
            },
        )