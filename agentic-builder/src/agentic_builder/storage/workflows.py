"""Workflow storage operations."""

import uuid
from datetime import datetime

from agentic_builder.core.constants import StageStatus, WorkflowStatus
from agentic_builder.storage.database import get_db


def generate_workflow_id() -> str:
    """Generate a unique workflow ID.

    Returns:
        Workflow ID in format wf_YYYYMMDD_HHMMSS_XXXXXXXX
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    short_uuid = uuid.uuid4().hex[:8]
    return f"wf_{timestamp}_{short_uuid}"


def create_workflow(
    workflow_type: str,
    description: str,
) -> str:
    """Create a new workflow run.

    Args:
        workflow_type: Type of workflow (full_project, add_feature, fix_bug)
        description: User-provided description

    Returns:
        Generated workflow ID
    """
    db = get_db()
    workflow_id = generate_workflow_id()
    db.execute_write(
        """
        INSERT INTO workflow_runs (id, workflow_type, description, status)
        VALUES (?, ?, ?, ?)
        """,
        (workflow_id, workflow_type, description, WorkflowStatus.PENDING.value),
    )
    return workflow_id


def get_workflow(workflow_id: str) -> dict | None:
    """Get workflow by ID.

    Args:
        workflow_id: Workflow identifier

    Returns:
        Workflow dictionary or None
    """
    db = get_db()
    row = db.execute_one("SELECT * FROM workflow_runs WHERE id = ?", (workflow_id,))
    return dict(row) if row else None


def get_latest_workflow() -> dict | None:
    """Get the most recent workflow.

    Returns:
        Most recent workflow dictionary or None
    """
    db = get_db()
    row = db.execute_one(
        "SELECT * FROM workflow_runs ORDER BY created_at DESC LIMIT 1"
    )
    return dict(row) if row else None


def get_workflows(status: str | None = None, limit: int = 20) -> list[dict]:
    """Get workflows with optional status filter.

    Args:
        status: Optional status filter
        limit: Maximum number of workflows to return

    Returns:
        List of workflow dictionaries
    """
    db = get_db()
    if status:
        rows = db.execute(
            "SELECT * FROM workflow_runs WHERE status = ? ORDER BY created_at DESC LIMIT ?",
            (status, limit),
        )
    else:
        rows = db.execute(
            "SELECT * FROM workflow_runs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
    return [dict(row) for row in rows]


def update_workflow_status(
    workflow_id: str,
    status: WorkflowStatus,
    error_message: str | None = None,
) -> None:
    """Update workflow status.

    Args:
        workflow_id: Workflow identifier
        status: New workflow status
        error_message: Optional error message for failed workflows
    """
    db = get_db()
    now = datetime.utcnow().isoformat()
    if status == WorkflowStatus.RUNNING:
        db.execute_write(
            "UPDATE workflow_runs SET status = ?, started_at = ?, updated_at = ? WHERE id = ?",
            (status.value, now, now, workflow_id),
        )
    elif status == WorkflowStatus.COMPLETED:
        db.execute_write(
            "UPDATE workflow_runs SET status = ?, completed_at = ?, updated_at = ? WHERE id = ?",
            (status.value, now, now, workflow_id),
        )
    elif error_message:
        db.execute_write(
            "UPDATE workflow_runs SET status = ?, error_message = ?, updated_at = ? WHERE id = ?",
            (status.value, error_message, now, workflow_id),
        )
    else:
        db.execute_write(
            "UPDATE workflow_runs SET status = ?, updated_at = ? WHERE id = ?",
            (status.value, now, workflow_id),
        )


def add_tokens_to_workflow(workflow_id: str, tokens: int, cost: float) -> None:
    """Add token usage to workflow total.

    Args:
        workflow_id: Workflow identifier
        tokens: Number of tokens to add
        cost: Cost in USD to add
    """
    db = get_db()
    db.execute_write(
        """
        UPDATE workflow_runs
        SET total_tokens_used = total_tokens_used + ?,
            estimated_cost_usd = estimated_cost_usd + ?,
            updated_at = ?
        WHERE id = ?
        """,
        (tokens, cost, datetime.utcnow().isoformat(), workflow_id),
    )


def create_stage(
    workflow_run_id: str,
    stage_name: str,
    stage_order: int,
    parallel: bool = False,
) -> str:
    """Create a workflow stage.

    Args:
        workflow_run_id: Parent workflow ID
        stage_name: Name of the stage
        stage_order: Order in the workflow (0-indexed)
        parallel: Whether agents in this stage run in parallel

    Returns:
        Generated stage ID
    """
    db = get_db()
    stage_id = f"{workflow_run_id}_stage_{stage_order:02d}"
    db.execute_write(
        """
        INSERT INTO workflow_stages (id, workflow_run_id, stage_name, stage_order, parallel, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            stage_id,
            workflow_run_id,
            stage_name,
            stage_order,
            int(parallel),
            StageStatus.PENDING.value,
        ),
    )
    return stage_id


def get_workflow_stages(workflow_run_id: str) -> list[dict]:
    """Get stages for a workflow.

    Args:
        workflow_run_id: Workflow identifier

    Returns:
        List of stage dictionaries ordered by stage_order
    """
    db = get_db()
    rows = db.execute(
        "SELECT * FROM workflow_stages WHERE workflow_run_id = ? ORDER BY stage_order",
        (workflow_run_id,),
    )
    return [dict(row) for row in rows]


def get_stage(stage_id: str) -> dict | None:
    """Get stage by ID.

    Args:
        stage_id: Stage identifier

    Returns:
        Stage dictionary or None
    """
    db = get_db()
    row = db.execute_one("SELECT * FROM workflow_stages WHERE id = ?", (stage_id,))
    return dict(row) if row else None


def update_stage_status(stage_id: str, status: StageStatus) -> None:
    """Update stage status.

    Args:
        stage_id: Stage identifier
        status: New stage status
    """
    db = get_db()
    now = datetime.utcnow().isoformat()
    if status == StageStatus.RUNNING:
        db.execute_write(
            "UPDATE workflow_stages SET status = ?, started_at = ? WHERE id = ?",
            (status.value, now, stage_id),
        )
    elif status in (StageStatus.COMPLETED, StageStatus.FAILED, StageStatus.SKIPPED):
        db.execute_write(
            "UPDATE workflow_stages SET status = ?, completed_at = ? WHERE id = ?",
            (status.value, now, stage_id),
        )
    else:
        db.execute_write(
            "UPDATE workflow_stages SET status = ? WHERE id = ?",
            (status.value, stage_id),
        )


def get_next_pending_stage(workflow_run_id: str) -> dict | None:
    """Get the next pending stage for a workflow.

    Args:
        workflow_run_id: Workflow identifier

    Returns:
        Next pending stage dictionary or None
    """
    db = get_db()
    row = db.execute_one(
        """
        SELECT * FROM workflow_stages
        WHERE workflow_run_id = ? AND status = ?
        ORDER BY stage_order LIMIT 1
        """,
        (workflow_run_id, StageStatus.PENDING.value),
    )
    return dict(row) if row else None
