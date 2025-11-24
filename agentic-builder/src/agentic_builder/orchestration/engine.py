"""Workflow execution engine."""

from typing import Awaitable, Callable

from agentic_builder.core.constants import StageStatus, WorkflowStatus
from agentic_builder.core.exceptions import WorkflowNotFoundError
from agentic_builder.orchestration.stage_executor import execute_stage
from agentic_builder.orchestration.workflows import get_workflow
from agentic_builder.storage import tasks as task_storage
from agentic_builder.storage import workflows as workflow_storage

EventHandler = Callable[[str, dict], Awaitable[None]]


class WorkflowEngine:
    """Orchestrates workflow execution."""

    def __init__(self):
        """Initialize the workflow engine."""
        self._event_handlers: dict[str, list[EventHandler]] = {}

    def on_event(self, event: str, handler: EventHandler) -> None:
        """Register an event handler.

        Args:
            event: Event name to handle
            handler: Async function to call when event occurs
        """
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)

    async def _emit(self, event: str, data: dict) -> None:
        """Emit an event to handlers.

        Args:
            event: Event name
            data: Event data dictionary
        """
        handlers = self._event_handlers.get(event, [])
        for handler in handlers:
            await handler(event, data)

    async def create_and_execute(
        self,
        workflow_type: str,
        description: str,
    ) -> str:
        """Create and execute a workflow.

        Args:
            workflow_type: Type of workflow to execute
            description: User-provided description

        Returns:
            Workflow ID

        Raises:
            WorkflowNotFoundError: If workflow type is unknown
        """
        # Get workflow definition
        workflow_def = get_workflow(workflow_type)
        if not workflow_def:
            raise WorkflowNotFoundError(f"Unknown workflow type: {workflow_type}")

        # Create workflow run
        workflow_id = workflow_storage.create_workflow(workflow_type, description)

        # Create stages
        stage_ids = []
        for i, stage_def in enumerate(workflow_def.stages):
            stage_id = workflow_storage.create_stage(
                workflow_run_id=workflow_id,
                stage_name=stage_def.name,
                stage_order=i,
                parallel=stage_def.parallel,
            )
            stage_ids.append(stage_id)

        # Create initial task for first agent
        first_stage = workflow_def.stages[0]
        first_agent = first_stage.agent_types[0]
        task_storage.create_task(
            task_id=f"{workflow_id}_task_001",
            workflow_run_id=workflow_id,
            title=f"Analyze requirements: {description[:100]}",
            agent_type=first_agent.value,
            description=description,
            priority="high",
            stage_id=stage_ids[0] if stage_ids else None,
            created_by="user",
        )

        # Execute workflow
        await self.execute(workflow_id)
        return workflow_id

    async def execute(self, workflow_id: str) -> None:
        """Execute a workflow.

        Args:
            workflow_id: Workflow identifier

        Raises:
            WorkflowNotFoundError: If workflow not found
        """
        workflow = workflow_storage.get_workflow(workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(f"Workflow not found: {workflow_id}")

        workflow_storage.update_workflow_status(workflow_id, WorkflowStatus.RUNNING)
        await self._emit("workflow_started", {"workflow_id": workflow_id})

        try:
            stages = workflow_storage.get_workflow_stages(workflow_id)

            for stage in stages:
                # Skip completed stages (for resume)
                if stage["status"] == StageStatus.COMPLETED.value:
                    continue

                # Update stage status
                workflow_storage.update_stage_status(stage["id"], StageStatus.RUNNING)
                await self._emit(
                    "stage_started",
                    {
                        "workflow_id": workflow_id,
                        "stage_id": stage["id"],
                        "stage_name": stage["stage_name"],
                    },
                )

                # Execute stage
                success = await execute_stage(
                    workflow_id=workflow_id,
                    stage_id=stage["id"],
                    parallel=bool(stage["parallel"]),
                )

                if success:
                    workflow_storage.update_stage_status(
                        stage["id"], StageStatus.COMPLETED
                    )
                    await self._emit(
                        "stage_completed",
                        {
                            "workflow_id": workflow_id,
                            "stage_id": stage["id"],
                        },
                    )
                else:
                    workflow_storage.update_stage_status(
                        stage["id"], StageStatus.FAILED
                    )
                    await self._emit(
                        "stage_failed",
                        {
                            "workflow_id": workflow_id,
                            "stage_id": stage["id"],
                        },
                    )
                    # Stop on failure
                    workflow_storage.update_workflow_status(
                        workflow_id,
                        WorkflowStatus.FAILED,
                        error_message=f"Stage {stage['stage_name']} failed",
                    )
                    await self._emit(
                        "workflow_failed", {"workflow_id": workflow_id}
                    )
                    return

            # All stages completed
            workflow_storage.update_workflow_status(
                workflow_id, WorkflowStatus.COMPLETED
            )
            await self._emit("workflow_completed", {"workflow_id": workflow_id})

        except Exception as e:
            workflow_storage.update_workflow_status(
                workflow_id, WorkflowStatus.FAILED, error_message=str(e)
            )
            await self._emit(
                "workflow_failed",
                {
                    "workflow_id": workflow_id,
                    "error": str(e),
                },
            )
            raise

    async def pause(self, workflow_id: str) -> None:
        """Pause a running workflow.

        Args:
            workflow_id: Workflow identifier
        """
        workflow_storage.update_workflow_status(workflow_id, WorkflowStatus.PAUSED)
        await self._emit("workflow_paused", {"workflow_id": workflow_id})

    async def resume(self, workflow_id: str) -> None:
        """Resume a paused workflow.

        Args:
            workflow_id: Workflow identifier

        Raises:
            WorkflowNotFoundError: If workflow not found
            ValueError: If workflow cannot be resumed
        """
        workflow = workflow_storage.get_workflow(workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(f"Workflow not found: {workflow_id}")
        if workflow["status"] not in (
            WorkflowStatus.PAUSED.value,
            WorkflowStatus.FAILED.value,
        ):
            raise ValueError(
                f"Cannot resume workflow in status: {workflow['status']}"
            )
        await self.execute(workflow_id)

    async def cancel(self, workflow_id: str) -> None:
        """Cancel a workflow.

        Args:
            workflow_id: Workflow identifier
        """
        workflow_storage.update_workflow_status(workflow_id, WorkflowStatus.CANCELLED)
        await self._emit("workflow_cancelled", {"workflow_id": workflow_id})
