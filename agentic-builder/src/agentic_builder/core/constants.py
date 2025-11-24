"""Constants and enums for agentic-builder."""

from enum import Enum


class AgentType(str, Enum):
    """Agent type identifiers."""

    PM = "PM"
    ARCH = "ARCH"
    RESEARCH = "RESEARCH"
    GD = "GD"
    UIUX = "UIUX"
    CQR = "CQR"
    SR = "SR"
    QE = "QE"
    E2E = "E2E"
    TQR = "TQR"
    DOE = "DOE"
    # Dynamic types (created at runtime)
    TL_PYTHON = "TL_PYTHON"
    TL_JAVASCRIPT = "TL_JAVASCRIPT"
    DEV_PYTHON = "DEV_PYTHON"
    DEV_JAVASCRIPT = "DEV_JAVASCRIPT"


class ModelTier(str, Enum):
    """Claude model tiers."""

    HAIKU = "haiku"
    SONNET = "sonnet"
    OPUS = "opus"


class WorkflowStatus(str, Enum):
    """Workflow execution status."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class StageStatus(str, Enum):
    """Stage execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


# Model mapping
AGENT_MODEL_TIERS: dict[AgentType, ModelTier] = {
    AgentType.PM: ModelTier.SONNET,
    AgentType.ARCH: ModelTier.OPUS,
    AgentType.RESEARCH: ModelTier.SONNET,
    AgentType.GD: ModelTier.SONNET,
    AgentType.UIUX: ModelTier.SONNET,
    AgentType.CQR: ModelTier.SONNET,
    AgentType.SR: ModelTier.OPUS,
    AgentType.QE: ModelTier.SONNET,
    AgentType.E2E: ModelTier.SONNET,
    AgentType.TQR: ModelTier.HAIKU,
    AgentType.DOE: ModelTier.SONNET,
    AgentType.TL_PYTHON: ModelTier.SONNET,
    AgentType.TL_JAVASCRIPT: ModelTier.SONNET,
    AgentType.DEV_PYTHON: ModelTier.SONNET,
    AgentType.DEV_JAVASCRIPT: ModelTier.SONNET,
}

# Token costs (per million tokens, 2025)
TOKEN_COSTS = {
    ModelTier.HAIKU: {"input": 0.25, "output": 1.25},
    ModelTier.SONNET: {"input": 3.0, "output": 15.0},
    ModelTier.OPUS: {"input": 15.0, "output": 75.0},
}

# Budget defaults
DEFAULT_WORKFLOW_BUDGET = 500_000
DEFAULT_AGENT_BUDGET = 50_000
BUDGET_WARNING_THRESHOLD = 0.8

# Context windowing
MAX_CHARS_PER_DEPENDENCY = 8000
MAX_TOTAL_CONTEXT_CHARS = 32000
SUMMARY_TARGET_CHARS = 1000

# Model aliases for Claude Code CLI
MODEL_ALIASES = {
    ModelTier.HAIKU: ["haiku", "haiku-4.5"],
    ModelTier.SONNET: ["sonnet", "sonnet-4.5"],
    ModelTier.OPUS: ["opus", "opus-4.1"],
}
