from typing import Self

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from apps.database.session import get_session_factory
from apps.repositories.agent_step_repository import AgentStepRepository
from apps.repositories.artifact_repository import ArtifactRepository
from apps.repositories.feedback_repository import FeedbackRepository
from apps.repositories.workflow_repository import WorkflowRepository


class UnitOfWork:
    """
    Coordinates repositories that participate in the same database transaction.

    A single UnitOfWork owns exactly one AsyncSession. All repositories created
    through it share that session, ensuring every database operation belongs to
    the same transaction.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        self._session_factory = (
            session_factory if session_factory is not None else get_session_factory()
        )

        self._session: AsyncSession | None = None

        self._workflow_repository: WorkflowRepository | None = None
        self._agent_step_repository: AgentStepRepository | None = None
        self._artifact_repository: ArtifactRepository | None = None
        self._feedback_repository: FeedbackRepository | None = None

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        return self

    async def __aexit__(
        self,
        exc_type,
        exc,
        tb,
    ) -> None:
        if self._session is None:
            return

        try:
            if exc_type is None:
                await self._session.commit()
            else:
                await self._session.rollback()
        finally:
            await self._session.close()

            self._session = None
            self._workflow_repository = None
            self._agent_step_repository = None
            self._artifact_repository = None
            self._feedback_repository = None

    @property
    def workflows(self) -> WorkflowRepository:
        if self._session is None:
            raise RuntimeError("UnitOfWork has not been entered.")

        if self._workflow_repository is None:
            self._workflow_repository = WorkflowRepository(self._session)

        return self._workflow_repository

    @property
    def agent_steps(self) -> AgentStepRepository:
        if self._session is None:
            raise RuntimeError("UnitOfWork has not been entered.")

        if self._agent_step_repository is None:
            self._agent_step_repository = AgentStepRepository(self._session)

        return self._agent_step_repository

    @property
    def artifacts(self) -> ArtifactRepository:
        if self._session is None:
            raise RuntimeError("UnitOfWork has not been entered.")

        if self._artifact_repository is None:
            self._artifact_repository = ArtifactRepository(self._session)

        return self._artifact_repository

    @property
    def feedback(self) -> FeedbackRepository:
        if self._session is None:
            raise RuntimeError("UnitOfWork has not been entered.")

        if self._feedback_repository is None:
            self._feedback_repository = FeedbackRepository(self._session)

        return self._feedback_repository

    async def rollback(self) -> None:
        if self._session is None:
            raise RuntimeError("UnitOfWork has not been entered.")

        await self._session.rollback()
