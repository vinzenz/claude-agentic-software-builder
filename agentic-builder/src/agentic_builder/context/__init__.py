"""Context module - XML serialization, windowing, and budget tracking."""

from agentic_builder.context.serializer import build_task_context, dict_to_xml, escape_xml
from agentic_builder.context.windowing import (
    apply_windowing,
    estimate_tokens,
    truncate_to_summary,
)
from agentic_builder.context.budget import (
    calculate_cost,
    check_budget,
    get_workflow_usage,
    is_budget_warning,
    record_usage,
)

__all__ = [
    "build_task_context",
    "dict_to_xml",
    "escape_xml",
    "apply_windowing",
    "estimate_tokens",
    "truncate_to_summary",
    "calculate_cost",
    "check_budget",
    "get_workflow_usage",
    "is_budget_warning",
    "record_usage",
]
