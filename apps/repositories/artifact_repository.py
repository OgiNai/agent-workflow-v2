from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.database.models import Artifact


class ArtifactRepository:
    """Persistence operations for Artifact entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, artifact: Artifact) -> Artifact:
        """Persist a workflow artifact."""
        self._session.add(artifact)
        await self._session.flush()
        # await self._session.refresh(artifact)
        return artifact

    async def list_by_workflow(
        self,
        workflow_id: uuid.UUID,
    ) -> list[Artifact]:
        """Return all artifacts for a workflow."""
        statement = (
            select(Artifact)
            .where(Artifact.workflow_id == workflow_id)
            .order_by(Artifact.created_at)
        )

        result = await self._session.execute(statement)
        return list(result.scalars().all())
