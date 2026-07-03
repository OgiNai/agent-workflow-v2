"""Shared domain exceptions."""


class WorkflowError(RuntimeError):
    """Raised when a workflow step fails in a controlled way."""


class ToolExecutionError(RuntimeError):
    """Raised when a deterministic tool fails."""


class AgentExecutionError(RuntimeError):
    """Raised when an LLM agent call fails."""
