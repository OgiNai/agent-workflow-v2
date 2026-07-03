"""Health/readiness endpoints."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from apps.settings import get_auth_settings

router = APIRouter(tags=["system"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/ready")
async def ready():
    try:
        settings = get_auth_settings()
        missing = []
        if not settings.api_token.get_secret_value():
            missing.append("API_TOKEN")
        if not settings.gemini_api_key.get_secret_value():
            missing.append("GEMINI_API_KEY")
        if not settings.project_path:
            missing.append("PROJECT_PATH")
        if missing:
            return JSONResponse(status_code=503, content={"status": "not_ready", "missing": missing})
        return {"status": "ready", "checks": {"config": "ok"}}
    except Exception as exc:
        return JSONResponse(status_code=503, content={"status": "not_ready", "reason": str(exc)})
