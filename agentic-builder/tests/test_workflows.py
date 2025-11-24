"""Tests for workflow storage operations."""

import pytest

from agentic_builder.core.constants import StageStatus, WorkflowStatus
from agentic_builder.storage import workflows as workflow_storage


class TestWorkflowCreation:
    """Test workflow creation operations."""

    def test_generate_workflow_id(self):
        """Test workflow ID generation."""
        workflow_id = workflow_storage.generate_workflow_id()

        # Should start with wf_
        assert workflow_id.startswith("wf_")

        # Should contain timestamp and UUID parts
        parts = workflow_id.split("_")
        assert len(parts) == 4  # wf, date, time, uuid
        assert len(parts[1]) == 8  # YYYYMMDD
        assert len(parts[2]) == 6  # HHMMSS
        assert len(parts[3]) == 8  # Short UUID

    def test_create_workflow(self):
        """Test creating a new workflow."""
        workflow_type = "full_project"
        description = "Test workflow description"

        workflow_id = workflow_storage.create_workflow(workflow_type, description)

        # Verify workflow was created
        workflow = workflow_storage.get_workflow(workflow_id)
        assert workflow is not None
        assert workflow["id"] == workflow_id
        assert workflow["workflow_type"] == workflow_type
        assert workflow["description"] == description
        assert workflow["status"] == WorkflowStatus.PENDING.value

    def test_get_workflow(self):
        """Test retrieving a workflow."""
        # Create a workflow first
        workflow_id = workflow_storage.create_workflow("test_type", "test desc")

        # Retrieve it
        workflow = workflow_storage.get_workflow(workflow_id)
        assert workflow is not None
        assert workflow["id"] == workflow_id

        # Try to get non-existent workflow
        nonexistent = workflow_storage.get_workflow("nonexistent_id")
        assert nonexistent is None

    def test_get_latest_workflow(self):
        """Test getting the most recent workflow."""
        # Create multiple workflows with a small delay to ensure different timestamps
        id1 = workflow_storage.create_workflow("type1", "desc1")
        import time
        time.sleep(0.01)  # Small delay to ensure different timestamps
        id2 = workflow_storage.create_workflow("type2", "desc2")

        # Latest should be one of the workflows we just created
        latest = workflow_storage.get_latest_workflow()
        assert latest is not None
        assert latest["id"] in [id1, id2]  # Should be one of the created workflows

        # And it should have the correct type and description
        if latest["id"] == id1:
            assert latest["workflow_type"] == "type1"
            assert latest["description"] == "desc1"
        elif latest["id"] == id2:
            assert latest["workflow_type"] == "type2"
            assert latest["description"] == "desc2"

    def test_get_workflows(self):
        """Test getting workflows with filters."""
        # Create test workflows
        id1 = workflow_storage.create_workflow("running", "desc1")
        id2 = workflow_storage.create_workflow("completed", "desc2")
        id3 = workflow_storage.create_workflow("running", "desc3")

        # Update statuses
        workflow_storage.update_workflow_status(id1, WorkflowStatus.RUNNING)
        workflow_storage.update_workflow_status(id2, WorkflowStatus.COMPLETED)
        workflow_storage.update_workflow_status(id3, WorkflowStatus.RUNNING)

        # Get all workflows
        all_workflows = workflow_storage.get_workflows()
        assert len(all_workflows) >= 3

        # Get running workflows
        running_workflows = workflow_storage.get_workflows(status=WorkflowStatus.RUNNING.value)
        assert len(running_workflows) >= 2
        for wf in running_workflows:
            assert wf["status"] == WorkflowStatus.RUNNING.value

        # Get completed workflows
        completed_workflows = workflow_storage.get_workflows(status=WorkflowStatus.COMPLETED.value)
        assert len(completed_workflows) >= 1
        for wf in completed_workflows:
            assert wf["status"] == WorkflowStatus.COMPLETED.value

    def test_update_workflow_status(self):
        """Test updating workflow status."""
        workflow_id = workflow_storage.create_workflow("test", "desc")

        # Update to running
        workflow_storage.update_workflow_status(workflow_id, WorkflowStatus.RUNNING)
        workflow = workflow_storage.get_workflow(workflow_id)
        assert workflow["status"] == WorkflowStatus.RUNNING.value
        assert workflow["started_at"] is not None

        # Update to completed
        workflow_storage.update_workflow_status(workflow_id, WorkflowStatus.COMPLETED)
        workflow = workflow_storage.get_workflow(workflow_id)
        assert workflow["status"] == WorkflowStatus.COMPLETED.value
        assert workflow["completed_at"] is not None

        # Update with error
        error_msg = "Test error"
        workflow_storage.update_workflow_status(
            workflow_id, WorkflowStatus.FAILED, error_message=error_msg
        )
        workflow = workflow_storage.get_workflow(workflow_id)
        assert workflow["status"] == WorkflowStatus.FAILED.value
        assert workflow["error_message"] == error_msg


class TestStageOperations:
    """Test workflow stage operations."""

    def test_create_stage(self):
        """Test creating a workflow stage."""
        workflow_id = workflow_storage.create_workflow("test", "desc")

        stage_name = "Requirements Gathering"
        stage_order = 0
        parallel = False

        stage_id = workflow_storage.create_stage(
            workflow_run_id=workflow_id,
            stage_name=stage_name,
            stage_order=stage_order,
            parallel=parallel,
        )

        # Verify stage was created
        stage = workflow_storage.get_stage(stage_id)
        assert stage is not None
        assert stage["id"] == stage_id
        assert stage["workflow_run_id"] == workflow_id
        assert stage["stage_name"] == stage_name
        assert stage["stage_order"] == stage_order
        assert stage["parallel"] == parallel
        assert stage["status"] == StageStatus.PENDING.value

    def test_get_workflow_stages(self):
        """Test getting stages for a workflow."""
        workflow_id = workflow_storage.create_workflow("test", "desc")

        # Create multiple stages
        stage_ids = []
        for i in range(3):
            stage_id = workflow_storage.create_stage(
                workflow_run_id=workflow_id,
                stage_name=f"Stage {i}",
                stage_order=i,
                parallel=(i == 1),  # Make stage 1 parallel
            )
            stage_ids.append(stage_id)

        # Get stages
        stages = workflow_storage.get_workflow_stages(workflow_id)
        assert len(stages) == 3

        # Should be ordered by stage_order
        for i, stage in enumerate(stages):
            assert stage["stage_order"] == i
            assert stage["stage_name"] == f"Stage {i}"
            assert stage["parallel"] == (i == 1)

    def test_update_stage_status(self):
        """Test updating stage status."""
        workflow_id = workflow_storage.create_workflow("test", "desc")
        stage_id = workflow_storage.create_stage(
            workflow_run_id=workflow_id,
            stage_name="Test Stage",
            stage_order=0,
        )

        # Update to running
        workflow_storage.update_stage_status(stage_id, StageStatus.RUNNING)
        stage = workflow_storage.get_stage(stage_id)
        assert stage["status"] == StageStatus.RUNNING.value
        assert stage["started_at"] is not None

        # Update to completed
        workflow_storage.update_stage_status(stage_id, StageStatus.COMPLETED)
        stage = workflow_storage.get_stage(stage_id)
        assert stage["status"] == StageStatus.COMPLETED.value
        assert stage["completed_at"] is not None

    def test_get_next_pending_stage(self):
        """Test getting the next pending stage."""
        workflow_id = workflow_storage.create_workflow("test", "desc")

        # Create stages
        stage1_id = workflow_storage.create_stage(
            workflow_run_id=workflow_id, stage_name="Stage 1", stage_order=0
        )
        stage2_id = workflow_storage.create_stage(
            workflow_run_id=workflow_id, stage_name="Stage 2", stage_order=1
        )

        # Initially, first stage should be next pending
        next_stage = workflow_storage.get_next_pending_stage(workflow_id)
        assert next_stage is not None
        assert next_stage["id"] == stage1_id

        # Mark first stage as completed
        workflow_storage.update_stage_status(stage1_id, StageStatus.COMPLETED)

        # Now second stage should be next pending
        next_stage = workflow_storage.get_next_pending_stage(workflow_id)
        assert next_stage is not None
        assert next_stage["id"] == stage2_id

        # Mark second stage as completed
        workflow_storage.update_stage_status(stage2_id, StageStatus.COMPLETED)

        # No more pending stages
        next_stage = workflow_storage.get_next_pending_stage(workflow_id)
        assert next_stage is None


class TestTokenTracking:
    """Test token usage tracking in workflows."""

    def test_add_tokens_to_workflow(self):
        """Test adding token usage to workflow totals."""
        workflow_id = workflow_storage.create_workflow("test", "desc")

        # Add some token usage
        workflow_storage.add_tokens_to_workflow(workflow_id, tokens=1000, cost=5.50)

        # Check workflow was updated
        workflow = workflow_storage.get_workflow(workflow_id)
        assert workflow["total_tokens_used"] == 1000
        assert workflow["estimated_cost_usd"] == 5.50

        # Add more usage
        workflow_storage.add_tokens_to_workflow(workflow_id, tokens=500, cost=2.75)

        # Check totals accumulated
        workflow = workflow_storage.get_workflow(workflow_id)
        assert workflow["total_tokens_used"] == 1500
        assert workflow["estimated_cost_usd"] == 8.25