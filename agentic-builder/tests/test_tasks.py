"""Tests for task storage operations."""



from agentic_builder.core.constants import TaskStatus
from agentic_builder.storage import tasks as task_storage
from agentic_builder.storage import workflows as workflow_storage


class TestTaskCreation:
    """Test task creation operations."""

    def test_create_task(self):
        """Test creating a new task."""
        workflow_id = workflow_storage.create_workflow("test_type", "test description")

        task_id = "test_task_001"
        title = "Test Task"
        agent_type = "PM"
        description = "Test description"
        priority = "high"
        created_by = "user"

        task_storage.create_task(
            task_id=task_id,
            workflow_run_id=workflow_id,
            title=title,
            agent_type=agent_type,
            description=description,
            priority=priority,
            created_by=created_by,
        )

        # Verify task was created
        task = task_storage.get_task(task_id)
        assert task is not None
        assert task["id"] == task_id
        assert task["workflow_run_id"] == workflow_id
        assert task["title"] == title
        assert task["agent_type"] == agent_type
        assert task["description"] == description
        assert task["priority"] == priority
        assert task["stage_id"] is None
        assert task["created_by"] == created_by
        assert task["status"] == TaskStatus.PENDING.value

    def test_get_task(self):
        """Test retrieving a task."""
        # Create a task first
        workflow_id = workflow_storage.create_workflow("test_type", "test description")
        task_id = "get_test_task"
        task_storage.create_task(
            task_id=task_id,
            workflow_run_id=workflow_id,
            title="Get Test Task",
            agent_type="PM",
        )

        # Retrieve it
        task = task_storage.get_task(task_id)
        assert task is not None
        assert task["id"] == task_id

        # Try to get non-existent task
        nonexistent = task_storage.get_task("nonexistent_task")
        assert nonexistent is None


class TestTaskQueries:
    """Test task query operations."""

    def test_get_workflow_tasks(self):
        """Test getting tasks for a workflow."""
        workflow_id = workflow_storage.create_workflow("test_type", "test description")

        # Create multiple tasks
        task_ids = []
        for i in range(3):
            task_id = f"query_task_{i}"
            task_storage.create_task(
                task_id=task_id,
                workflow_run_id=workflow_id,
                title=f"Task {i}",
                agent_type="PM",
                priority="medium" if i % 2 == 0 else "high",
            )
            task_ids.append(task_id)

        # Get all tasks for workflow
        tasks = task_storage.get_workflow_tasks(workflow_id)
        assert len(tasks) == 3

        # Get tasks by status
        # First update one task status
        task_storage.update_task_status(task_ids[0], TaskStatus.COMPLETED)

        completed_tasks = task_storage.get_workflow_tasks(workflow_id, status=TaskStatus.COMPLETED.value)
        assert len(completed_tasks) == 1
        assert completed_tasks[0]["id"] == task_ids[0]

        pending_tasks = task_storage.get_workflow_tasks(workflow_id, status=TaskStatus.PENDING.value)
        assert len(pending_tasks) == 2

    def test_get_stage_tasks(self):
        """Test getting tasks for a stage."""
        workflow_id = workflow_storage.create_workflow("test_type", "test description")
        stage_id = workflow_storage.create_stage(workflow_id, "test_stage", 0)

        # Create tasks for the stage
        task_ids = []
        for i in range(2):
            task_id = f"stage_task_{i}"
            task_storage.create_task(
                task_id=task_id,
                workflow_run_id=workflow_id,
                stage_id=stage_id,
                title=f"Stage Task {i}",
                agent_type="PM",
            )
            task_ids.append(task_id)

        # Get tasks for stage
        stage_tasks = task_storage.get_stage_tasks(stage_id)
        assert len(stage_tasks) == 2
        for task in stage_tasks:
            assert task["stage_id"] == stage_id

        # Get tasks by status
        task_storage.update_task_status(task_ids[0], TaskStatus.RUNNING)
        running_tasks = task_storage.get_stage_tasks(stage_id, status=TaskStatus.RUNNING.value)
        assert len(running_tasks) == 1
        assert running_tasks[0]["id"] == task_ids[0]


class TestTaskStatusUpdates:
    """Test task status update operations."""

    def test_update_task_status_basic(self):
        """Test basic task status updates."""
        workflow_id = workflow_storage.create_workflow("test_type", "test description")
        task_id = "status_test_task"
        task_storage.create_task(
            task_id=task_id,
            workflow_run_id=workflow_id,
            title="Status Test",
            agent_type="PM",
        )

        # Update to running
        task_storage.update_task_status(task_id, TaskStatus.RUNNING)
        task = task_storage.get_task(task_id)
        assert task["status"] == TaskStatus.RUNNING.value

        # Update to completed
        task_storage.update_task_status(task_id, TaskStatus.COMPLETED)
        task = task_storage.get_task(task_id)
        assert task["status"] == TaskStatus.COMPLETED.value
        assert task["completed_at"] is not None

        # Update with error
        error_msg = "Test error"
        task_storage.update_task_status(task_id, TaskStatus.FAILED, error_message=error_msg)
        task = task_storage.get_task(task_id)
        assert task["status"] == TaskStatus.FAILED.value
        assert task["error_message"] == error_msg


class TestTaskDependencies:
    """Test task dependency operations."""

    def test_add_task_dependency(self):
        """Test adding task dependencies."""
        workflow_id = workflow_storage.create_workflow("test_type", "test description")
        task_id = "dependent_task"
        depends_on_id = "dependency_task"

        # Create both tasks
        task_storage.create_task(
            task_id=task_id,
            workflow_run_id=workflow_id,
            title="Dependent Task",
            agent_type="PM",
        )
        task_storage.create_task(
            task_id=depends_on_id,
            workflow_run_id=workflow_id,
            title="Dependency Task",
            agent_type="PM",
        )

        # Add dependency
        task_storage.add_task_dependency(task_id, depends_on_id)

        # Verify dependency was added
        dependencies = task_storage.get_task_dependencies(task_id)
        assert depends_on_id in dependencies

    def test_get_task_dependencies(self):
        """Test retrieving task dependencies."""
        workflow_id = workflow_storage.create_workflow("test_type", "test description")
        task_id = "multi_dep_task"

        # Create task
        task_storage.create_task(
            task_id=task_id,
            workflow_run_id=workflow_id,
            title="Multi Dep Task",
            agent_type="PM",
        )

        # Create multiple dependencies
        dep_ids = []
        for i in range(3):
            dep_id = f"dep_{i}"
            task_storage.create_task(
                task_id=dep_id,
                workflow_run_id=workflow_id,
                title=f"Dependency {i}",
                agent_type="PM",
            )
            task_storage.add_task_dependency(task_id, dep_id)
            dep_ids.append(dep_id)

        # Get dependencies
        dependencies = task_storage.get_task_dependencies(task_id)
        assert len(dependencies) == 3
        for dep_id in dep_ids:
            assert dep_id in dependencies

    def test_get_runnable_tasks(self):
        """Test getting tasks that are ready to run."""
        workflow_id = workflow_storage.create_workflow("test_type", "test description")

        # Create tasks with dependencies
        task1_id = "runnable_task1"
        task2_id = "runnable_task2"
        task3_id = "runnable_task3"

        task_storage.create_task(
            task_id=task1_id,
            workflow_run_id=workflow_id,
            title="Task 1",
            agent_type="PM",
        )
        task_storage.create_task(
            task_id=task2_id,
            workflow_run_id=workflow_id,
            title="Task 2",
            agent_type="PM",
        )
        task_storage.create_task(
            task_id=task3_id,
            workflow_run_id=workflow_id,
            title="Task 3",
            agent_type="PM",
        )

        # Task 2 depends on Task 1
        task_storage.add_task_dependency(task2_id, task1_id)
        # Task 3 depends on Task 2
        task_storage.add_task_dependency(task3_id, task2_id)

        # Initially, only Task 1 should be runnable
        runnable = task_storage.get_runnable_tasks(workflow_id)
        runnable_ids = [t["id"] for t in runnable]
        assert task1_id in runnable_ids
        assert task2_id not in runnable_ids
        assert task3_id not in runnable_ids

        # Mark Task 1 as completed
        task_storage.update_task_status(task1_id, TaskStatus.COMPLETED)

        # Now Task 2 should be runnable
        runnable = task_storage.get_runnable_tasks(workflow_id)
        runnable_ids = [t["id"] for t in runnable]
        assert task1_id not in runnable_ids  # Completed, not runnable
        assert task2_id in runnable_ids
        assert task3_id not in runnable_ids

        # Mark Task 2 as completed
        task_storage.update_task_status(task2_id, TaskStatus.COMPLETED)

        # Now Task 3 should be runnable
        runnable = task_storage.get_runnable_tasks(workflow_id)
        runnable_ids = [t["id"] for t in runnable]
        assert task3_id in runnable_ids


class TestTaskContext:
    """Test task context operations."""

    def test_save_and_get_task_context(self):
        """Test saving and retrieving task context."""
        workflow_id = workflow_storage.create_workflow("test_type", "test description")
        task_id = "context_task"
        context_xml = '<context><summary>Test context</summary></context>'
        token_count = 150

        # Create task first
        task_storage.create_task(
            task_id=task_id,
            workflow_run_id=workflow_id,
            title="Context Task",
            agent_type="PM",
        )

        # Save context
        task_storage.save_task_context(task_id, context_xml, token_count)

        # Retrieve context
        retrieved_context = task_storage.get_task_context(task_id)
        assert retrieved_context == context_xml

    def test_get_nonexistent_task_context(self):
        """Test getting context for task without context."""
        nonexistent_context = task_storage.get_task_context("nonexistent_task")
        assert nonexistent_context is None


class TestTaskOutput:
    """Test task output operations."""

    def test_save_and_get_task_output(self):
        """Test saving and retrieving task output."""
        workflow_id = workflow_storage.create_workflow("test_type", "test description")
        task_id = "output_task"
        output_xml = '<output><success>true</success><summary>Task completed</summary></output>'
        summary = "Task completed successfully"
        key_decisions = ["Decision 1", "Decision 2"]
        artifacts = [
            {"type": "code", "name": "test.py", "description": "Test file", "content": "print('hello')"}
        ]
        tokens_used = 500
        model_used = "sonnet"

        # Create task first
        task_storage.create_task(
            task_id=task_id,
            workflow_run_id=workflow_id,
            title="Output Task",
            agent_type="PM",
        )

        # Save output
        task_storage.save_task_output(
            task_id=task_id,
            output_xml=output_xml,
            summary=summary,
            key_decisions=key_decisions,
            artifacts=artifacts,
            tokens_used=tokens_used,
            model_used=model_used,
        )

        # Retrieve output
        output = task_storage.get_task_output(task_id)
        assert output is not None
        assert output["task_id"] == task_id
        assert output["output_xml"] == output_xml
        assert output["summary"] == summary
        assert output["key_decisions"] == key_decisions
        assert output["artifacts"] == artifacts
        assert output["tokens_used"] == tokens_used
        assert output["model_used"] == model_used

    def test_get_nonexistent_task_output(self):
        """Test getting output for task without output."""
        nonexistent_output = task_storage.get_task_output("nonexistent_task")
        assert nonexistent_output is None

    def test_task_output_json_serialization(self):
        """Test that JSON fields are properly serialized/deserialized."""
        workflow_id = workflow_storage.create_workflow("test_type", "test description")
        task_id = "json_task"

        # Create task
        task_storage.create_task(
            task_id=task_id,
            workflow_run_id=workflow_id,
            title="JSON Task",
            agent_type="PM",
        )

        # Save output with complex data
        key_decisions = ["Decision with 'quotes'", 'Decision with "double quotes"']
        artifacts = [
            {
                "type": "code",
                "name": "complex.py",
                "description": "Complex file with special chars: <>&\"",
                "content": "def func():\n    return 'hello & goodbye'"
            }
        ]

        task_storage.save_task_output(
            task_id=task_id,
            output_xml="<output></output>",
            summary="Complex output",
            key_decisions=key_decisions,
            artifacts=artifacts,
            tokens_used=100,
            model_used="opus",
        )

        # Retrieve and verify JSON parsing
        output = task_storage.get_task_output(task_id)
        assert output["key_decisions"] == key_decisions
        assert output["artifacts"] == artifacts