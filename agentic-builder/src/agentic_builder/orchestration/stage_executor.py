"""Stage execution with parallel/sequential support."""

import asyncio

from agentic_builder.agents.executor import execute_agent
from agentic_builder.context.serializer import build_task_context
from agentic_builder.core.constants import AgentType, TaskStatus
from agentic_builder.storage import tasks as task_storage


async def execute_stage(
    workflow_id: str,
    stage_id: str,
    parallel: bool = False,
) -> bool:
    """Execute all tasks in a stage.

    Args:
        workflow_id: Workflow identifier
        stage_id: Stage identifier
        parallel: Whether to execute tasks in parallel

    Returns:
        True if all tasks completed successfully
    """
    # Get runnable tasks for this stage
    stage_tasks = task_storage.get_stage_tasks(stage_id, status=TaskStatus.PENDING.value)

    if not stage_tasks:
        # No tasks in this stage, check if there are any runnable tasks in workflow
        runnable = task_storage.get_runnable_tasks(workflow_id)
        stage_tasks = [t for t in runnable if t.get("stage_id") == stage_id]

    if not stage_tasks:
        # No tasks to execute, stage is complete
        return True

    if parallel:
        # Execute tasks in parallel
        results = await asyncio.gather(
            *[execute_task(t) for t in stage_tasks],
            return_exceptions=True,
        )
        return all(not isinstance(r, Exception) and r for r in results)
    else:
        # Execute tasks sequentially
        for task in stage_tasks:
            success = await execute_task(task)
            if not success:
                return False
        return True


async def execute_task(task: dict) -> bool:
    """Execute a single task.

    Args:
        task: Task dictionary from storage

    Returns:
        True if task completed successfully
    """
    task_id = task["id"]
    workflow_id = task["workflow_run_id"]

    # Parse agent type
    try:
        agent_type = AgentType(task["agent_type"])
    except ValueError:
        # Handle dynamic agent types
        agent_type_str = task["agent_type"]
        if agent_type_str.startswith("DEV_"):
            agent_type = AgentType.DEV_PYTHON
        elif agent_type_str.startswith("TL_"):
            agent_type = AgentType.TL_PYTHON
        else:
            agent_type = AgentType.PM  # Fallback

    # Build context from dependencies
    dependencies = task_storage.get_task_dependencies(task_id)
    dep_outputs = []
    for dep_id in dependencies:
        output = task_storage.get_task_output(dep_id)
        if output:
            dep_task = task_storage.get_task(dep_id)
            dep_outputs.append(
                {
                    "task_id": dep_id,
                    "agent_type": dep_task["agent_type"] if dep_task else "",
                    "summary": output.get("summary", ""),
                    "key_decisions": output.get("key_decisions", []),
                }
            )

    # Build context XML
    context_xml = build_task_context(
        task_id=task_id,
        agent_type=agent_type.value,
        workflow_id=workflow_id,
        summary=task.get("title", ""),
        requirements=[task.get("description", "")] if task.get("description") else [],
        constraints=[],
        dependencies=dep_outputs,
        artifacts=[],
        acceptance_criteria=[],
    )

    # Save context
    task_storage.save_task_context(task_id, context_xml, len(context_xml) // 4)

    # Execute agent
    try:
        response = await execute_agent(
            task_id=task_id,
            agent_type=agent_type,
            workflow_run_id=workflow_id,
            context_xml=context_xml,
        )
        return response.success
    except Exception:
        return False
