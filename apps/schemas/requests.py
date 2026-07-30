"""API request schemas."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from apps.core.constants import DEFAULT_MAX_ROUNDS, MAX_ROUNDS_LIMIT

TaskType = Literal["auto", "generate", "review_refactor"]
#InputType = Literal["auto", "inline_code", "file_path", "natural_language"]


class ReviewRequest(BaseModel):
    """Unified request for code generation, review, refactoring, and repair workflows."""

    task_type: TaskType = "auto"
    #input_type: InputType = "auto"
    instruction: str = Field(
        ..., 
        min_length=1, 
        description=(
            "Natural-language feature request or instructions "
            "for reviewing/refactoring existing code."
        )
    )
    code: str | None = Field(default=None, description="Existing source code supplied inline.")
    file_path: str | None = Field(default=None, description="Path to an existing source file.")
    max_rounds: int = Field(default=DEFAULT_MAX_ROUNDS, ge=1, le=MAX_ROUNDS_LIMIT)
    save_artifacts: bool = True

    @model_validator(mode="after")  
    def validate_request(self) -> "ReviewRequest":
        has_code = self.code is not None and bool(self.code.strip())
        has_file = self.file_path is not None and bool(self.file_path.strip())
        has_source = has_code or has_file

        if has_code and has_file:
            raise ValueError("Provide either code or file_path, not both.")

        if self.task_type == "generate" and has_source:
            raise ValueError("task_type='generate' cannot include existing source code.")

        if self.task_type == "review_refactor" and not has_source:
            raise ValueError("task_type='review_refactor' requires code or file_path.")
        
        return self


class FeedbackRequest(BaseModel):
    """Human feedback for a completed workflow run."""

    rating: int = Field(..., ge=1, le=5)
    accepted: bool
    comment: str | None = None
