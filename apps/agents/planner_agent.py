"""Planner agent.

Milestone 1 keeps this deterministic to avoid wasting LLM calls on routing. The class still exposes an
agent-like interface and records a planner step, so it can be switched to an LLM planner later.
"""

import time

from apps.schemas.workflow import RouterResult, WorkflowPlan


class PlannerAgent:
    agent_name = "planner"

    async def run(
        self, router_result: RouterResult, max_rounds: int
    ) -> tuple[WorkflowPlan, int]:
        started = time.perf_counter()
        requires_generation = router_result.task_type == "generate"
        steps = []
        if requires_generation:
            steps.append("code_writer.generate")
        steps.extend(
            [
                "inspection.reviewer",
                "inspection.security_auditor",
                "code_writer.refactor_or_repair",
                "test_generator",
                "test_runner",
                "evaluator",
            ]
        )
        plan = WorkflowPlan(
            task_type=router_result.task_type,
            requires_generation=requires_generation,
            requires_refactor=True,
            requires_tests=True,
            max_rounds=max_rounds,
            steps=steps,
            notes=["Deterministic planner used for Milestone 1."],
        )
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        return plan, latency_ms
