"""FastAPI security dependencies."""

import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from apps.core.settings import get_auth_settings

security = HTTPBearer()

BearerCredentials = Annotated[
    HTTPAuthorizationCredentials,
    Depends(security),
]


async def verify_bearer_token(
    credentials: BearerCredentials,
) -> None:
    """Validate the configured API bearer token."""
    if credentials.scheme != "Bearer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid authentication scheme",
        )

    expected_token = get_auth_settings().api_token.get_secret_value()
    if not secrets.compare_digest(credentials.credentials, expected_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )
