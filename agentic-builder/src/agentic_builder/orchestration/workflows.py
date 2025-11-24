"""Predefined workflow definitions."""

from dataclasses import dataclass

from agentic_builder.core.constants import AgentType


@dataclass
class StageDefinition:
    """Definition of a workflow stage."""

    name: str
    agent_types: list[AgentType]
    parallel: bool = False


@dataclass
class WorkflowDefinition:
    """Definition of a complete workflow."""

    id: str
    name: str
    description: str
    stages: list[StageDefinition]


WORKFLOWS: dict[str, WorkflowDefinition] = {
    "full_project": WorkflowDefinition(
        id="full_project",
        name="Full Project",
        description="Complete project from idea to implementation",
        stages=[
            StageDefinition("requirements", [AgentType.PM]),
            StageDefinition("research", [AgentType.RESEARCH]),
            StageDefinition("architecture", [AgentType.ARCH]),
            StageDefinition("design", [AgentType.GD, AgentType.UIUX], parallel=True),
            StageDefinition("task_review", [AgentType.TQR]),
            StageDefinition(
                "implementation", [AgentType.DEV_PYTHON], parallel=True
            ),  # Dynamic
            StageDefinition(
                "quality", [AgentType.CQR, AgentType.SR, AgentType.QE], parallel=True
            ),
            StageDefinition("e2e_testing", [AgentType.E2E]),
        ],
    ),
    "add_feature": WorkflowDefinition(
        id="add_feature",
        name="Add Feature",
        description="Add a feature to existing project",
        stages=[
            StageDefinition("requirements", [AgentType.PM]),
            StageDefinition("architecture", [AgentType.ARCH]),
            StageDefinition("task_review", [AgentType.TQR]),
            StageDefinition(
                "implementation", [AgentType.DEV_PYTHON], parallel=True
            ),
            StageDefinition("quality", [AgentType.CQR, AgentType.QE], parallel=True),
        ],
    ),
    "fix_bug": WorkflowDefinition(
        id="fix_bug",
        name="Fix Bug",
        description="Diagnose and fix a bug",
        stages=[
            StageDefinition("analysis", [AgentType.RESEARCH]),
            StageDefinition("solution", [AgentType.ARCH]),
            StageDefinition("implementation", [AgentType.DEV_PYTHON]),
            StageDefinition(
                "verification", [AgentType.QE, AgentType.E2E], parallel=True
            ),
        ],
    ),
    "security_audit": WorkflowDefinition(
        id="security_audit",
        name="Security Audit",
        description="Comprehensive security review of codebase",
        stages=[
            StageDefinition("analysis", [AgentType.RESEARCH]),
            StageDefinition("security_review", [AgentType.SR]),
            StageDefinition("quality_review", [AgentType.CQR]),
        ],
    ),
}


def get_workflow(workflow_type: str) -> WorkflowDefinition | None:
    """Get a workflow definition by type.

    Args:
        workflow_type: Workflow type identifier

    Returns:
        WorkflowDefinition or None if not found
    """
    return WORKFLOWS.get(workflow_type)


def list_workflows() -> list[WorkflowDefinition]:
    """List all available workflows.

    Returns:
        List of all WorkflowDefinition objects
    """
    return list(WORKFLOWS.values())
