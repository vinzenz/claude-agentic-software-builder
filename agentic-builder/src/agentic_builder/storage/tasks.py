"""Task storage operations."""

import json
from datetime import datetime

from agentic_builder.core.constants import TaskStatus
from agentic_builder.storage.database import get_db


def create_task(
    task_id: str,
    workflow_run_id: str,
    title: str,
    agent_type: str,
    description: str = "",
    priority: str = "medium",
    stage_id: str | None = None,
    created_by: str | None = None,
) -> None:
    """Create a new task.

    Args:
        task_id: Unique task identifier
        workflow_run_id: Parent workflow ID
        title: Task title
        agent_type: Agent type to execute this task
        description: Task description
        priority: Task priority (low, medium, high)
        stage_id: Optional stage ID
        created_by: Creator identifier (agent type or 'user')
    """
    db = get_db()
    db.execute_write(
        """
        INSERT INTO tasks (id, workflow_run_id, stage_id, title, description,
                          status, priority, agent_type, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            task_id,
            workflow_run_id,
            stage_id,
            title,
            description,
            TaskStatus.PENDING.value,
            priority,
            agent_type,
            created_by,
        ),
    )


def get_task(task_id: str) -> dict | None:
    """Get task by ID.

    Args:
        task_id: Task identifier

    Returns:
        Task dictionary or None if not found
    """
    db = get_db()
    row = db.execute_one("SELECT * FROM tasks WHERE id = ?", (task_id,))
    return dict(row) if row else None


def get_workflow_tasks(
    workflow_run_id: str, status: str | None = None
) -> list[dict]:
    """Get tasks for a workflow.

    Args:
        workflow_run_id: Workflow identifier
        status: Optional status filter

    Returns:
        List of task dictionaries
    """
    db = get_db()
    if status:
        rows = db.execute(
            "SELECT * FROM tasks WHERE workflow_run_id = ? AND status = ? ORDER BY created_at",
            (workflow_run_id, status),
        )
    else:
        rows = db.execute(
            "SELECT * FROM tasks WHERE workflow_run_id = ? ORDER BY created_at",
            (workflow_run_id,),
        )
    return [dict(row) for row in rows]


def get_stage_tasks(stage_id: str, status: str | None = None) -> list[dict]:
    """Get tasks for a stage.

    Args:
        stage_id: Stage identifier
        status: Optional status filter

    Returns:
        List of task dictionaries
    """
    db = get_db()
    if status:
        rows = db.execute(
            "SELECT * FROM tasks WHERE stage_id = ? AND status = ? ORDER BY created_at",
            (stage_id, status),
        )
    else:
        rows = db.execute(
            "SELECT * FROM tasks WHERE stage_id = ? ORDER BY created_at",
            (stage_id,),
        )
    return [dict(row) for row in rows]


def update_task_status(
    task_id: str, status: TaskStatus, error_message: str | None = None
) -> None:
    """Update task status.

    Args:
        task_id: Task identifier
        status: New task status
        error_message: Optional error message for failed tasks
    """
    db = get_db()
    now = datetime.utcnow().isoformat()
    if status == TaskStatus.COMPLETED:
        db.execute_write(
            "UPDATE tasks SET status = ?, completed_at = ?, updated_at = ? WHERE id = ?",
            (status.value, now, now, task_id),
        )
    elif error_message:
        db.execute_write(
            "UPDATE tasks SET status = ?, error_message = ?, updated_at = ? WHERE id = ?",
            (status.value, error_message, now, task_id),
        )
    else:
        db.execute_write(
            "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
            (status.value, now, task_id),
        )


def add_task_dependency(task_id: str, depends_on_task_id: str) -> None:
    """Add a dependency between tasks.

    Args:
        task_id: Dependent task ID
        depends_on_task_id: Task ID that must complete first
    """
    db = get_db()
    db.execute_write(
        "INSERT OR IGNORE INTO task_dependencies (task_id, depends_on_task_id) VALUES (?, ?)",
        (task_id, depends_on_task_id),
    )


def get_task_dependencies(task_id: str) -> list[str]:
    """Get task IDs this task depends on.

    Args:
        task_id: Task identifier

    Returns:
        List of dependency task IDs
    """
    db = get_db()
    rows = db.execute(
        "SELECT depends_on_task_id FROM task_dependencies WHERE task_id = ?",
        (task_id,),
    )
    return [row["depends_on_task_id"] for row in rows]


def get_runnable_tasks(workflow_run_id: str) -> list[dict]:
    """Get tasks that are ready to run (all dependencies completed).

    Args:
        workflow_run_id: Workflow identifier

    Returns:
        List of runnable task dictionaries
    """
    db = get_db()
    rows = db.execute(
        """
        SELECT t.* FROM tasks t
        WHERE t.workflow_run_id = ?
          AND t.status = 'pending'
          AND NOT EXISTS (
            SELECT 1 FROM task_dependencies td
            JOIN tasks dt ON td.depends_on_task_id = dt.id
            WHERE td.task_id = t.id AND dt.status != 'completed'
          )
        """,
        (workflow_run_id,),
    )
    return [dict(row) for row in rows]


def save_task_context(task_id: str, context_xml: str, token_count: int) -> None:
    """Save task context.

    Args:
        task_id: Task identifier
        context_xml: XML context string
        token_count: Estimated token count
    """
    db = get_db()
    db.execute_write(
        """
        INSERT OR REPLACE INTO task_context (task_id, context_xml, context_tokens)
        VALUES (?, ?, ?)
        """,
        (task_id, context_xml, token_count),
    )


def get_task_context(task_id: str) -> str | None:
    """Get task context XML.

    Args:
        task_id: Task identifier

    Returns:
        Context XML string or None
    """
    db = get_db()
    row = db.execute_one(
        "SELECT context_xml FROM task_context WHERE task_id = ?", (task_id,)
    )
    return row["context_xml"] if row else None


def save_task_output(
    task_id: str,
    output_xml: str,
    summary: str,
    key_decisions: list[str],
    artifacts: list[dict],
    tokens_used: int,
    model_used: str,
) -> None:
    """Save task output.

    Args:
        task_id: Task identifier
        output_xml: Raw XML output
        summary: Output summary
        key_decisions: List of key decisions made
        artifacts: List of artifact dictionaries
        tokens_used: Total tokens used
        model_used: Model used for execution
    """
    db = get_db()
    db.execute_write(
        """
        INSERT OR REPLACE INTO task_outputs
        (task_id, output_xml, summary, key_decisions, artifacts, tokens_used, model_used)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            task_id,
            output_xml,
            summary,
            json.dumps(key_decisions),
            json.dumps(artifacts),
            tokens_used,
            model_used,
        ),
    )


def get_task_output(task_id: str) -> dict | None:
    """Get task output.

    Args:
        task_id: Task identifier

    Returns:
        Output dictionary with parsed JSON fields, or None
    """
    db = get_db()
    row = db.execute_one("SELECT * FROM task_outputs WHERE task_id = ?", (task_id,))
    if row:
        result = dict(row)
        result["key_decisions"] = json.loads(result["key_decisions"] or "[]")
        result["artifacts"] = json.loads(result["artifacts"] or "[]")
        return result
    return None
