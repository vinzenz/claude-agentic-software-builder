"""Tests for token budget tracking."""

import pytest

from agentic_builder.context.budget import (
    calculate_cost,
    check_budget,
    get_workflow_usage,
    is_budget_warning,
    record_usage,
)
from agentic_builder.core.constants import ModelTier


class TestCalculateCost:
    """Test cost calculation functions."""

    def test_calculate_cost_haiku(self):
        """Test cost calculation for Haiku model."""
        cost = calculate_cost(ModelTier.HAIKU, 1000, 500)
        expected = (1000 / 1_000_000) * 0.25 + (500 / 1_000_000) * 1.25
        assert cost == pytest.approx(expected, rel=1e-6)

    def test_calculate_cost_sonnet(self):
        """Test cost calculation for Sonnet model."""
        cost = calculate_cost(ModelTier.SONNET, 2000, 1000)
        expected = (2000 / 1_000_000) * 3.0 + (1000 / 1_000_000) * 15.0
        assert cost == pytest.approx(expected, rel=1e-6)

    def test_calculate_cost_opus(self):
        """Test cost calculation for Opus model."""
        cost = calculate_cost(ModelTier.OPUS, 1500, 800)
        expected = (1500 / 1_000_000) * 15.0 + (800 / 1_000_000) * 75.0
        assert cost == pytest.approx(expected, rel=1e-6)

    def test_calculate_cost_zero_tokens(self):
        """Test cost calculation with zero tokens."""
        cost = calculate_cost(ModelTier.SONNET, 0, 0)
        assert cost == 0.0


class TestRecordUsage:
    """Test token usage recording."""

    def test_record_usage_basic(self):
        """Test basic usage recording."""
        from agentic_builder.storage import workflows as workflow_storage
        from agentic_builder.storage import tasks as task_storage

        # Create a workflow and task first
        workflow_id = workflow_storage.create_workflow("test_type", "test description")
        task_id = task_storage.create_task(
            task_id="test_task_456",
            workflow_run_id=workflow_id,
            title="Test Task",
            agent_type="DEV_PYTHON",
        )

        agent_type = "DEV_PYTHON"
        model = "sonnet"

        cost = record_usage(
            workflow_run_id=workflow_id,
            task_id=task_id,
            agent_type=agent_type,
            model=model,
            input_tokens=1000,
            output_tokens=500,
        )

        expected_cost = calculate_cost(ModelTier.SONNET, 1000, 500)
        assert cost == pytest.approx(expected_cost, rel=1e-6)

    def test_record_usage_with_model_alias(self):
        """Test usage recording with different model aliases."""
        from agentic_builder.storage import workflows as workflow_storage
        from agentic_builder.storage import tasks as task_storage

        workflow_id = workflow_storage.create_workflow("test_type", "test description")

        # Test haiku-3.5
        task_id_haiku = task_storage.create_task(
            task_id="task_haiku",
            workflow_run_id=workflow_id,
            title="Haiku Task",
            agent_type="TQR",
        )
        cost_haiku = record_usage(
            workflow_run_id=workflow_id,
            task_id=task_id_haiku,
            agent_type="TQR",
            model="haiku-4.5",
            input_tokens=500,
            output_tokens=200,
        )
        expected_haiku = calculate_cost(ModelTier.HAIKU, 500, 200)
        assert cost_haiku == pytest.approx(expected_haiku, rel=1e-6)

        # Test opus-3
        task_id_opus = task_storage.create_task(
            task_id="task_opus",
            workflow_run_id=workflow_id,
            title="Opus Task",
            agent_type="ARCH",
        )
        cost_opus = record_usage(
            workflow_run_id=workflow_id,
            task_id=task_id_opus,
            agent_type="ARCH",
            model="opus-4.1",
            input_tokens=800,
            output_tokens=400,
        )
        expected_opus = calculate_cost(ModelTier.OPUS, 800, 400)
        assert cost_opus == pytest.approx(expected_opus, rel=1e-6)

    def test_record_usage_unknown_model(self):
        """Test usage recording with unknown model (defaults to sonnet)."""
        from agentic_builder.storage import workflows as workflow_storage
        from agentic_builder.storage import tasks as task_storage

        workflow_id = workflow_storage.create_workflow("test_type", "test description")
        task_id = task_storage.create_task(
            task_id="task_unknown",
            workflow_run_id=workflow_id,
            title="Unknown Task",
            agent_type="UNKNOWN",
        )

        cost = record_usage(
            workflow_run_id=workflow_id,
            task_id=task_id,
            agent_type="UNKNOWN",
            model="unknown-model",
            input_tokens=1000,
            output_tokens=500,
        )

        # Should default to sonnet pricing
        expected_cost = calculate_cost(ModelTier.SONNET, 1000, 500)
        assert cost == pytest.approx(expected_cost, rel=1e-6)


class TestBudgetChecking:
    """Test budget checking functions."""

    def test_check_budget_under_limit(self):
        """Test budget check when under limit."""
        from agentic_builder.storage import workflows as workflow_storage
        from agentic_builder.storage import tasks as task_storage

        workflow_id = workflow_storage.create_workflow("test_type", "test description")
        task_id = task_storage.create_task(
            task_id="task_budget_1",
            workflow_run_id=workflow_id,
            title="Budget Task 1",
            agent_type="PM",
        )

        # Record some usage
        record_usage(
            workflow_run_id=workflow_id,
            task_id=task_id,
            agent_type="PM",
            model="sonnet",
            input_tokens=10000,
            output_tokens=5000,
        )

        within_budget, percent = check_budget(workflow_id, budget=50000)
        assert within_budget is True
        assert percent < 1.0

    def test_check_budget_over_limit(self):
        """Test budget check when over limit."""
        from agentic_builder.storage import workflows as workflow_storage
        from agentic_builder.storage import tasks as task_storage

        workflow_id = workflow_storage.create_workflow("test_type", "test description")
        task_id = task_storage.create_task(
            task_id="task_budget_2",
            workflow_run_id=workflow_id,
            title="Budget Task 2",
            agent_type="PM",
        )

        # Record high usage
        record_usage(
            workflow_run_id=workflow_id,
            task_id=task_id,
            agent_type="PM",
            model="sonnet",
            input_tokens=100000,
            output_tokens=50000,
        )

        within_budget, percent = check_budget(workflow_id, budget=50000)
        assert within_budget is False
        assert percent > 1.0

    def test_check_budget_at_limit(self):
        """Test budget check exactly at limit."""
        from agentic_builder.storage import workflows as workflow_storage
        from agentic_builder.storage import tasks as task_storage

        workflow_id = workflow_storage.create_workflow("test_type", "test description")
        task_id = task_storage.create_task(
            task_id="task_budget_3",
            workflow_run_id=workflow_id,
            title="Budget Task 3",
            agent_type="PM",
        )

        # Test with a budget of 1000 tokens
        budget = 1000
        # Use exactly 1000 input tokens (should be at budget limit)
        record_usage(
            workflow_run_id=workflow_id,
            task_id=task_id,
            agent_type="PM",
            model="sonnet",
            input_tokens=budget,
            output_tokens=0,
        )

        within_budget, percent = check_budget(workflow_id, budget=budget)
        # Should be exactly at limit
        assert within_budget is False  # At limit is not within budget
        assert percent == 1.0

    def test_is_budget_warning(self):
        """Test budget warning detection."""
        from agentic_builder.storage import workflows as workflow_storage
        from agentic_builder.storage import tasks as task_storage

        workflow_id = workflow_storage.create_workflow("test_type", "test description")
        task_id = task_storage.create_task(
            task_id="task_warning",
            workflow_run_id=workflow_id,
            title="Warning Task",
            agent_type="PM",
        )

        # Record usage at 85% of budget (above warning threshold of 80%)
        budget = 10000  # tokens
        warning_tokens = int(budget * 0.85)  # 8500 tokens

        record_usage(
            workflow_run_id=workflow_id,
            task_id=task_id,
            agent_type="PM",
            model="sonnet",
            input_tokens=warning_tokens,
            output_tokens=0,
        )

        assert is_budget_warning(workflow_id, budget=budget) is True

        # Test below warning threshold
        workflow_id_low = workflow_storage.create_workflow("test_type", "test description")
        task_id_low = task_storage.create_task(
            task_id="task_low",
            workflow_run_id=workflow_id_low,
            title="Low Task",
            agent_type="PM",
        )
        low_tokens = int(budget * 0.7)  # 7000 tokens, below 80% threshold

        record_usage(
            workflow_run_id=workflow_id_low,
            task_id=task_id_low,
            agent_type="PM",
            model="sonnet",
            input_tokens=low_tokens,
            output_tokens=0,
        )

        assert is_budget_warning(workflow_id_low, budget=budget) is False


class TestWorkflowUsage:
    """Test workflow usage retrieval."""

    def test_get_workflow_usage_empty(self):
        """Test getting usage for workflow with no records."""
        workflow_id = "empty_workflow"
        usage = get_workflow_usage(workflow_id)

        assert usage["total_input"] == 0
        assert usage["total_output"] == 0
        assert usage["total_tokens"] == 0
        assert usage["total_cost"] == 0.0

    def test_get_workflow_usage_with_data(self):
        """Test getting usage for workflow with token records."""
        from agentic_builder.storage import workflows as workflow_storage
        from agentic_builder.storage import tasks as task_storage

        workflow_id = workflow_storage.create_workflow("test_type", "test description")
        task_id_1 = task_storage.create_task(
            task_id="task_usage_1",
            workflow_run_id=workflow_id,
            title="Usage Task 1",
            agent_type="PM",
        )
        task_id_2 = task_storage.create_task(
            task_id="task_usage_2",
            workflow_run_id=workflow_id,
            title="Usage Task 2",
            agent_type="ARCH",
        )

        # Record multiple usages
        record_usage(
            workflow_run_id=workflow_id,
            task_id=task_id_1,
            agent_type="PM",
            model="sonnet",
            input_tokens=1000,
            output_tokens=500,
        )

        record_usage(
            workflow_run_id=workflow_id,
            task_id=task_id_2,
            agent_type="ARCH",
            model="opus",
            input_tokens=800,
            output_tokens=400,
        )

        usage = get_workflow_usage(workflow_id)

        assert usage["total_input"] == 1800
        assert usage["total_output"] == 900
        assert usage["total_tokens"] == 2700
        assert usage["total_cost"] > 0

        # Verify cost calculation
        expected_cost = calculate_cost(ModelTier.SONNET, 1000, 500) + calculate_cost(
            ModelTier.OPUS, 800, 400
        )
        assert usage["total_cost"] == pytest.approx(expected_cost, rel=1e-6)