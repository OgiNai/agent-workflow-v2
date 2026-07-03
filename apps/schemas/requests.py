"""API request schemas."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from apps.core.constants import DEFAULT_MAX_ROUNDS, MAX_ROUNDS_LIMIT

TaskType = Literal["auto", "generate", "review", "refactor", "review_refactor"]
InputType = Literal["auto", "inline_code", "file_path", "natural_language"]


class ReviewRequest(BaseModel):
    """Unified request for code generation, review, refactoring, and repair workflows."""

    task_type: TaskType = "auto"
    input_type: InputType = "auto"
    instruction: str = Field(..., min_length=1, description="User goal or instruction.")
    content: str | None = Field(default=None, description="Inline code or natural-language request.")
    file_path: str | None = Field(default=None, description="Relative path to a code file inside PROJECT_PATH.")
    max_rounds: int = Field(default=DEFAULT_MAX_ROUNDS, ge=1, le=MAX_ROUNDS_LIMIT)
    save_artifacts: bool = True

    @model_validator(mode="after")
    def validate_input_source(self) -> "ReviewRequest":
        if not self.content and not self.file_path:
            raise ValueError("Either content or file_path must be provided.")
        if self.input_type == "file_path" and not self.file_path:
            raise ValueError("file_path is required when input_type='file_path'.")
        if self.task_type == "generate" and self.file_path and not self.content:
            raise ValueError("task_type='generate' should use natural-language content, not only file_path.")
        return self


class FeedbackRequest(BaseModel):
    """Human feedback for a completed workflow run."""

    rating: int = Field(..., ge=1, le=5)
    accepted: bool
    comment: str | None = None
