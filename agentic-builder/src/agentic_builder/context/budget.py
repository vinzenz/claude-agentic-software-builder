"""Token budget tracking."""

from agentic_builder.core.constants import (
    BUDGET_WARNING_THRESHOLD,
    DEFAULT_WORKFLOW_BUDGET,
    TOKEN_COSTS,
    ModelTier,
)
from agentic_builder.storage.database import get_db


def calculate_cost(
    model_tier: ModelTier, input_tokens: int, output_tokens: int
) -> float:
    """Calculate cost in USD for token usage.

    Args:
        model_tier: Model tier (haiku, sonnet, opus)
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Cost in USD
    """
    costs = TOKEN_COSTS[model_tier]
    input_cost = (input_tokens / 1_000_000) * costs["input"]
    output_cost = (output_tokens / 1_000_000) * costs["output"]
    return input_cost + output_cost


def record_usage(
    workflow_run_id: str,
    task_id: str,
    agent_type: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """Record token usage and return cost.

    Args:
        workflow_run_id: Workflow identifier
        task_id: Task identifier
        agent_type: Agent type
        model: Model name/alias
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Calculated cost in USD
    """
    # Try to parse model tier from model string
    try:
        if "-" in model:
            tier_str = model.split("-")[1] if "-" in model else model
        else:
            tier_str = model
        model_tier = ModelTier(tier_str.lower())
    except ValueError:
        model_tier = ModelTier.SONNET  # Default to sonnet

    cost = calculate_cost(model_tier, input_tokens, output_tokens)

    db = get_db()
    db.execute_write(
        """
        INSERT INTO token_usage (workflow_run_id, task_id, agent_type, model, input_tokens, output_tokens, cost_usd)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (workflow_run_id, task_id, agent_type, model, input_tokens, output_tokens, cost),
    )
    return cost


def get_workflow_usage(workflow_run_id: str) -> dict:
    """Get token usage summary for a workflow.

    Args:
        workflow_run_id: Workflow identifier

    Returns:
        Dictionary with total_input, total_output, total_tokens, total_cost
    """
    db = get_db()
    row = db.execute_one(
        """
        SELECT
            SUM(input_tokens) as total_input,
            SUM(output_tokens) as total_output,
            SUM(cost_usd) as total_cost
        FROM token_usage
        WHERE workflow_run_id = ?
        """,
        (workflow_run_id,),
    )
    return {
        "total_input": row["total_input"] or 0,
        "total_output": row["total_output"] or 0,
        "total_tokens": (row["total_input"] or 0) + (row["total_output"] or 0),
        "total_cost": row["total_cost"] or 0.0,
    }


def check_budget(
    workflow_run_id: str, budget: int = DEFAULT_WORKFLOW_BUDGET
) -> tuple[bool, float]:
    """Check if workflow is within budget.

    Args:
        workflow_run_id: Workflow identifier
        budget: Token budget

    Returns:
        Tuple of (within_budget, usage_percent)
    """
    usage = get_workflow_usage(workflow_run_id)
    total = usage["total_tokens"]
    percent = total / budget if budget > 0 else 0
    return total < budget, percent


def is_budget_warning(
    workflow_run_id: str, budget: int = DEFAULT_WORKFLOW_BUDGET
) -> bool:
    """Check if budget warning threshold reached.

    Args:
        workflow_run_id: Workflow identifier
        budget: Token budget

    Returns:
        True if warning threshold reached
    """
    _within_budget, percent = check_budget(workflow_run_id, budget)
    return percent >= BUDGET_WARNING_THRESHOLD
