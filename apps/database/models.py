import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from apps.database.base import Base


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    instruction: Mapped[str] = mapped_column(Text)

    source_type: Mapped[str | None] = mapped_column(String(50))
    task_type: Mapped[str | None] = mapped_column(String(50))

    status: Mapped[str] = mapped_column(String(50))
    final_decision: Mapped[str | None] = mapped_column(String(50))

    summary: Mapped[str | None] = mapped_column(Text)

    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    duration_ms: Mapped[int | None] = mapped_column(Integer)

    rule_score: Mapped[float | None] = mapped_column(Float)
    execution_score: Mapped[float | None] = mapped_column(Float)
    llm_score: Mapped[float | None] = mapped_column(Float)
    security_score: Mapped[float | None] = mapped_column(Float)
    maintainability_score: Mapped[float | None] = mapped_column(Float)
    correctness_score: Mapped[float | None] = mapped_column(Float)
    overall_score: Mapped[float | None] = mapped_column(Float)

    metadata_json: Mapped[dict | None] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class AgentStep(Base):
    __tablename__ = "agent_steps"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflow_runs.id"),
    )

    iteration: Mapped[int] = mapped_column(Integer)
    step_order: Mapped[int] = mapped_column(Integer)

    agent_name: Mapped[str] = mapped_column(String(100))

    duration_ms: Mapped[int | None] = mapped_column(Integer)

    input_json: Mapped[dict | None] = mapped_column(JSON)
    output_json: Mapped[dict | None] = mapped_column(JSON)

    prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    completion_tokens: Mapped[int | None] = mapped_column(Integer)
    total_tokens: Mapped[int | None] = mapped_column(Integer)

    status: Mapped[str] = mapped_column(String(50))
    error: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflow_runs.id"),
    )

    artifact_type: Mapped[str] = mapped_column(String(50))
    relative_path: Mapped[str] = mapped_column(Text)

    size_bytes: Mapped[int | None] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class Feedback(Base):
    __tablename__ = "feedback"

    __table_args__ = (
        UniqueConstraint(
            "workflow_id",
            name="uq_feedback_workflow_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflow_runs.id"),
    )

    rating: Mapped[int | None] = mapped_column(Integer)
    accepted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    comments: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
