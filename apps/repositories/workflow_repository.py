from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.database.models import WorkflowRun


class WorkflowRepository:
    """Persistence operations for WorkflowRun entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, workflow: WorkflowRun) -> WorkflowRun:
        """Persist a new workflow run."""
        self._session.add(workflow)
        await self._session.commit()
        await self._session.refresh(workflow)
        return workflow

    async def get(self, workflow_id: uuid.UUID) -> WorkflowRun | None:
        """Retrieve a workflow by its identifier."""
        statement = select(WorkflowRun).where(
            WorkflowRun.id == workflow_id,
        )

        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def update(self, workflow: WorkflowRun) -> WorkflowRun:
        """
        Persist changes made to an existing workflow.

        The supplied ORM instance is assumed to already be attached
        to the current session.
        """
        await self._session.commit()
        await self._session.refresh(workflow)
        return workflow

    async def delete(self, workflow: WorkflowRun) -> None:
        """Delete a workflow run."""
        await self._session.delete(workflow)
        await self._session.commit()
