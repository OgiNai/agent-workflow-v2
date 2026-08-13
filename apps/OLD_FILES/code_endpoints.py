import secrets
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from starlette.responses import JSONResponse, Response

from apps.agent_with_tools import agent_result
from apps.core.settings import get_auth_settings
from apps.multi_agent_system import agents_result

router = APIRouter()

# Create security scheme
security = HTTPBearer()


class GenerateSchema(BaseModel):
    """Generate Schema"""

    generate_rounds: int
    generate_content: str


class ReviewSchema(BaseModel):
    """Review Schema"""

    review_content: str


"""
Becuase of the router, every endpoint in this file is prefixed with /code/
"""


@router.post("/generate")
async def generate_code(
    request_data: GenerateSchema,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Response:
    """
    Generates code by given user instructions.

    Args
        request_data:
            generate_rounds: maximum number of attempt rounds
            generate_content: text instructions for code generation
    """

    await verify_token(credentials)

    return await call_agent_system(request_data)


@router.post("/review")
async def review_code(
    request_data: ReviewSchema,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Response:
    """
    Reviews code by given user instructions.

    Args
        request_data:
            review_content: text instructions for code review
    """

    await verify_token(credentials)

    return await call_agent_system(request_data)


# helper functions


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> None:
    """
    Verify scheme is Bearer and token is correct

    Args:
        credentials: HTTPAuthorizationCredentials

    Raises:
        HTTPException: Invalid authentication scheme
        HTTPException: Invalid authentication token
    """
    if credentials.scheme != "Bearer":
        raise HTTPException(status_code=403, detail="Invalid authentication scheme")

    api_token = get_auth_settings().api_token.get_secret_value()

    if not secrets.compare_digest(credentials.credentials, api_token):
        raise HTTPException(status_code=401, detail="Invalid authentication token")


async def call_agent_system(request_data: ReviewSchema | GenerateSchema) -> Response:
    """
    Function to call either agent_with_tools.agent_result or multi_agent_system.agents_result

    Args:
        request_data: request data of type:
            ReviewSchema for review agent with tools or
            GenerateSchema for two-agents system

    Returns:
        Response from the agent system
    """
    # from apps.multi_agent_system import agents_result
    # from apps.agent_with_tools import agent_result

    try:
        if isinstance(request_data, ReviewSchema):
            result = await agent_result(request_data.review_content)
        else:
            result = await agents_result(
                request_data.generate_content, request_data.generate_rounds
            )

        # Return acceptance response
        return JSONResponse(content={"result": result}, status_code=HTTPStatus.ACCEPTED)
    except Exception as e:
        err_msg = (
            "reviewing" if isinstance(request_data, ReviewSchema) else "generation"
        )
        return JSONResponse(
            content={"result": f"Error calling code {err_msg} agents: {str(e)}"},
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )
