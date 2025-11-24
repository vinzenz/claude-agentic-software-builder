"""Tests for core constants and enums."""


from agentic_builder.core.constants import (
    AGENT_MODEL_TIERS,
    AgentType,
    BUDGET_WARNING_THRESHOLD,
    DEFAULT_AGENT_BUDGET,
    DEFAULT_WORKFLOW_BUDGET,
    MAX_CHARS_PER_DEPENDENCY,
    MAX_TOTAL_CONTEXT_CHARS,
    MODEL_ALIASES,
    ModelTier,
    StageStatus,
    SUMMARY_TARGET_CHARS,
    TaskStatus,
    TOKEN_COSTS,
    WorkflowStatus,
)


class TestEnums:
    """Test enum definitions."""

    def test_agent_type_values(self):
        """Test AgentType enum values."""
        assert AgentType.PM.value == "PM"
        assert AgentType.ARCH.value == "ARCH"
        assert AgentType.RESEARCH.value == "RESEARCH"
        assert AgentType.GD.value == "GD"
        assert AgentType.UIUX.value == "UIUX"
        assert AgentType.CQR.value == "CQR"
        assert AgentType.SR.value == "SR"
        assert AgentType.QE.value == "QE"
        assert AgentType.E2E.value == "E2E"
        assert AgentType.TQR.value == "TQR"
        assert AgentType.DOE.value == "DOE"
        assert AgentType.TL_PYTHON.value == "TL_PYTHON"
        assert AgentType.TL_JAVASCRIPT.value == "TL_JAVASCRIPT"
        assert AgentType.DEV_PYTHON.value == "DEV_PYTHON"
        assert AgentType.DEV_JAVASCRIPT.value == "DEV_JAVASCRIPT"

    def test_model_tier_values(self):
        """Test ModelTier enum values."""
        assert ModelTier.HAIKU.value == "haiku"
        assert ModelTier.SONNET.value == "sonnet"
        assert ModelTier.OPUS.value == "opus"

    def test_workflow_status_values(self):
        """Test WorkflowStatus enum values."""
        assert WorkflowStatus.PENDING.value == "pending"
        assert WorkflowStatus.RUNNING.value == "running"
        assert WorkflowStatus.PAUSED.value == "paused"
        assert WorkflowStatus.COMPLETED.value == "completed"
        assert WorkflowStatus.FAILED.value == "failed"
        assert WorkflowStatus.CANCELLED.value == "cancelled"

    def test_task_status_values(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.ASSIGNED.value == "assigned"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.BLOCKED.value == "blocked"

    def test_stage_status_values(self):
        """Test StageStatus enum values."""
        assert StageStatus.PENDING.value == "pending"
        assert StageStatus.RUNNING.value == "running"
        assert StageStatus.COMPLETED.value == "completed"
        assert StageStatus.FAILED.value == "failed"
        assert StageStatus.SKIPPED.value == "skipped"


class TestConstants:
    """Test constant values."""

    def test_token_costs(self):
        """Test token cost definitions."""
        assert TOKEN_COSTS[ModelTier.HAIKU]["input"] == 0.25
        assert TOKEN_COSTS[ModelTier.HAIKU]["output"] == 1.25
        assert TOKEN_COSTS[ModelTier.SONNET]["input"] == 3.0
        assert TOKEN_COSTS[ModelTier.SONNET]["output"] == 15.0
        assert TOKEN_COSTS[ModelTier.OPUS]["input"] == 15.0
        assert TOKEN_COSTS[ModelTier.OPUS]["output"] == 75.0

    def test_budget_constants(self):
        """Test budget-related constants."""
        assert DEFAULT_WORKFLOW_BUDGET == 500_000
        assert DEFAULT_AGENT_BUDGET == 50_000
        assert BUDGET_WARNING_THRESHOLD == 0.8

    def test_context_constants(self):
        """Test context windowing constants."""
        assert MAX_CHARS_PER_DEPENDENCY == 8000
        assert MAX_TOTAL_CONTEXT_CHARS == 32000
        assert SUMMARY_TARGET_CHARS == 1000

    def test_model_aliases(self):
        """Test model alias mappings."""
        assert "haiku" in MODEL_ALIASES[ModelTier.HAIKU]
        assert "haiku-4.5" in MODEL_ALIASES[ModelTier.HAIKU]
        assert "sonnet" in MODEL_ALIASES[ModelTier.SONNET]
        assert "sonnet-4.5" in MODEL_ALIASES[ModelTier.SONNET]
        assert "opus" in MODEL_ALIASES[ModelTier.OPUS]
        assert "opus-4.1" in MODEL_ALIASES[ModelTier.OPUS]


class TestAgentModelTiers:
    """Test agent model tier mappings."""

    def test_all_agents_have_model_tiers(self):
        """Test that all agent types have model tier assignments."""
        for agent_type in AgentType:
            assert agent_type in AGENT_MODEL_TIERS
            assert isinstance(AGENT_MODEL_TIERS[agent_type], ModelTier)

    def test_specific_agent_model_assignments(self):
        """Test specific agent model tier assignments."""
        assert AGENT_MODEL_TIERS[AgentType.PM] == ModelTier.SONNET
        assert AGENT_MODEL_TIERS[AgentType.ARCH] == ModelTier.OPUS
        assert AGENT_MODEL_TIERS[AgentType.SR] == ModelTier.OPUS
        assert AGENT_MODEL_TIERS[AgentType.TQR] == ModelTier.HAIKU