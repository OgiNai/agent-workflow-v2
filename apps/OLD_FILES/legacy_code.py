"""Temporary compatibility wrappers for old /code endpoints."""

from http import HTTPStatus

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from apps.core.security import verify_bearer_token
from apps.schemas.requests import ReviewRequest
from apps.workflows.code_workflow import run_code_workflow

router = APIRouter()


class GenerateSchema(BaseModel):
    generate_rounds: int = 2
    generate_content: str


class ReviewSchema(BaseModel):
    review_content: str


@router.post("/generate", status_code=HTTPStatus.ACCEPTED)
async def generate_code(request_data: GenerateSchema, _: None = Depends(verify_bearer_token)):
    result = await run_code_workflow(
        ReviewRequest(
            task_type="generate",
            #input_type="natural_language",
            instruction=request_data.generate_content,
            #content=request_data.generate_content,
            max_rounds=request_data.generate_rounds,
            save_artifacts=True,
        )
    )
    return result


@router.post("/review", status_code=HTTPStatus.ACCEPTED)
async def review_code(request_data: ReviewSchema, _: None = Depends(verify_bearer_token)):
    result = await run_code_workflow(
        ReviewRequest(
            task_type="review_refactor",
            #input_type="inline_code",
            instruction="Review and improve this code.",
            code=request_data.review_content,
            max_rounds=2,
            save_artifacts=True,
        )
    )
    return result
