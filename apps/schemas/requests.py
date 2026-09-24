"""API request schemas."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from apps.core.constants import (
    MAX_FILE_PATH_LENGTH,
    MAX_INLINE_CODE_LENGTH,
    MAX_INSTRUCTION_LENGTH,
    MAX_ROUNDS_LIMIT,
)
from apps.schemas.review_context import PRContext

TaskType = Literal["auto", "generate", "review_refactor"]


class ReviewRequest(BaseModel):
    """Unified request for code generation, review, refactoring, and repair workflows."""

    task_type: TaskType = "auto"
    instruction: str = Field(
        ...,
        min_length=1,
        max_length=MAX_INSTRUCTION_LENGTH,
        description=(
            "Natural-language feature request or instructions "
            "for reviewing/refactoring existing code."
        ),
    )
    code: str | None = Field(
        default=None,
        max_length=MAX_INLINE_CODE_LENGTH,
        description="Existing source code supplied inline.",
    )
    file_path: str | None = Field(
        default=None,
        max_length=MAX_FILE_PATH_LENGTH,
        description="Path to an existing source file.",
    )
    max_rounds: int | None = Field(default=None, ge=1, le=MAX_ROUNDS_LIMIT)
    save_artifacts: bool = True
    review_context: PRContext | None = None

    @model_validator(mode="after")
    def validate_request(self) -> "ReviewRequest":
        has_code = self.code is not None and bool(self.code.strip())
        has_file = self.file_path is not None and bool(self.file_path.strip())
        has_source = has_code or has_file

        if has_code and has_file:
            raise ValueError("Provide either code or file_path, not both.")

        if self.task_type == "generate" and has_source:
            raise ValueError(
                "task_type='generate' cannot include existing source code."
            )

        if self.task_type == "review_refactor" and not has_source:
            raise ValueError("task_type='review_refactor' requires code or file_path.")

        return self


class FeedbackRequest(BaseModel):
    """Human feedback for a completed workflow run."""

    rating: int = Field(..., ge=1, le=5)
    accepted: bool
    comment: str | None = None
