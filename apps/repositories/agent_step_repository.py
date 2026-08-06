from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.database.models import AgentStep


class AgentStepRepository:
    """Persistence operations for AgentStep entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, agent_step: AgentStep) -> AgentStep:
        """Persist a new agent step."""
        self._session.add(agent_step)
        await self._session.commit()
        await self._session.refresh(agent_step)
        return agent_step

    async def list_by_workflow(
        self,
        workflow_id: uuid.UUID,
    ) -> list[AgentStep]:
        """Return all agent steps for a workflow ordered by execution."""
        statement = (
            select(AgentStep)
            .where(AgentStep.workflow_id == workflow_id)
            .order_by(
                AgentStep.iteration,
                AgentStep.step_order,
            )
        )

        result = await self._session.execute(statement)
        return list(result.scalars().all())
