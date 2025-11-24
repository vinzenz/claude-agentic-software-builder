"""Model selection for agents based on task complexity."""

from agentic_builder.agents.registry import get_model_for_agent
from agentic_builder.core.constants import AgentType, ModelTier


def select_model(
    agent_type: AgentType,
    task_complexity: str = "medium",
    budget_remaining: float = 1.0,
) -> ModelTier:
    """Select appropriate model tier for a task.

    Args:
        agent_type: Type of agent executing the task
        task_complexity: Task complexity (low, medium, high)
        budget_remaining: Fraction of budget remaining (0.0-1.0)

    Returns:
        Selected ModelTier
    """
    # Get default model for agent
    default_model = get_model_for_agent(agent_type)

    # If budget is low, downgrade model
    if budget_remaining < 0.2:
        return ModelTier.HAIKU

    # If budget is medium-low and task is not critical, downgrade
    if budget_remaining < 0.5 and task_complexity != "high":
        if default_model == ModelTier.OPUS:
            return ModelTier.SONNET
        return default_model

    # High complexity tasks might upgrade
    if task_complexity == "high" and default_model == ModelTier.SONNET:
        # Only upgrade if we have budget
        if budget_remaining > 0.7:
            return ModelTier.OPUS

    return default_model


def estimate_task_complexity(task: dict) -> str:
    """Estimate task complexity based on description and type.

    Args:
        task: Task dictionary

    Returns:
        Complexity level (low, medium, high)
    """
    description = task.get("description", "") + " " + task.get("title", "")
    description_lower = description.lower()

    # High complexity indicators
    high_indicators = [
        "architecture",
        "design system",
        "security",
        "scale",
        "performance",
        "complex",
        "integration",
        "migrate",
    ]

    # Low complexity indicators
    low_indicators = [
        "simple",
        "basic",
        "update",
        "fix typo",
        "rename",
        "minor",
        "small",
    ]

    high_count = sum(1 for indicator in high_indicators if indicator in description_lower)
    low_count = sum(1 for indicator in low_indicators if indicator in description_lower)

    if high_count >= 2:
        return "high"
    elif low_count >= 2:
        return "low"
    elif high_count > low_count:
        return "high"
    elif low_count > high_count:
        return "low"

    return "medium"
