from __future__ import annotations

import pytest

from apps.database.models import WorkflowRun
from apps.database.session import close_database_engine
from apps.database.unit_of_work import UnitOfWork


@pytest.mark.anyio
async def test_commit() -> None:
    print("=== Commit test ===")

    async with UnitOfWork() as uow:
        workflow = WorkflowRun(
            instruction="Repository smoke test",
            source_type="inline",
            task_type="review",
            status="running",
        )

        await uow.workflows.create(workflow)

        workflow_id = workflow.id

        print(f"Created workflow: {workflow_id}")

    async with UnitOfWork() as uow:
        loaded = await uow.workflows.get(workflow_id)

        assert loaded is not None
        assert loaded.id == workflow_id

        assert loaded.created_at is not None
        assert loaded.updated_at is not None

        print("Workflow successfully committed.")


@pytest.mark.anyio
async def test_rollback() -> None:
    print("\n=== Rollback test ===")

    workflow_id = None

    try:
        async with UnitOfWork() as uow:
            workflow = WorkflowRun(
                instruction="Rollback test",
                source_type="inline",
                task_type="review",
                status="running",
            )

            await uow.workflows.create(workflow)

            workflow_id = workflow.id

            print(f"Created workflow: {workflow_id}")

            raise RuntimeError("Intentional rollback")

    except RuntimeError:
        pass

    async with UnitOfWork() as uow:
        loaded = await uow.workflows.get(workflow_id)

        assert loaded is None

        print("Rollback successful.")


@pytest.fixture(autouse=True)
async def cleanup_database_engine():
    yield
    await close_database_engine()


"""
async def main() -> None:
    await test_commit()
    await test_rollback()

    print("\nAll UnitOfWork tests passed.")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
"""
