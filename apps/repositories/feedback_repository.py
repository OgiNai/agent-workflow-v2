from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.database.models import Feedback


class FeedbackRepository:
    """Persistence operations for Feedback entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, feedback: Feedback) -> Feedback:
        """Persist workflow feedback."""
        self._session.add(feedback)
        await self._session.flush()
        return feedback

    async def get_by_workflow(
        self,
        workflow_id: uuid.UUID,
    ) -> Feedback | None:
        """Return feedback associated with a workflow."""
        statement = select(Feedback).where(
            Feedback.workflow_id == workflow_id,
        )

        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def update(self, feedback: Feedback) -> Feedback:
        """Persist changes made to existing workflow feedback."""
        await self._session.flush()
        return feedback
