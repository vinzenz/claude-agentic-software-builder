"""Custom exceptions for agentic-builder."""


class AgenticError(Exception):
    """Base exception for agentic-builder."""

    pass


class NotInitializedError(AgenticError):
    """Project not initialized."""

    pass


class WorkflowNotFoundError(AgenticError):
    """Workflow not found."""

    pass


class TaskNotFoundError(AgenticError):
    """Task not found."""

    pass


class AgentExecutionError(AgenticError):
    """Agent execution failed."""

    pass


class TokenBudgetExceededError(AgenticError):
    """Token budget exceeded."""

    pass


class ConfigurationError(AgenticError):
    """Configuration error."""

    pass
