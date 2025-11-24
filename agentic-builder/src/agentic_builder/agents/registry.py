"""Agent type registry and configuration."""

from dataclasses import dataclass

from agentic_builder.core.constants import AgentType, ModelTier


@dataclass
class AgentConfig:
    """Configuration for an agent type."""

    type: AgentType
    name: str
    description: str
    prompt_file: str
    model_tier: ModelTier
    capabilities: list[str]


AGENT_CONFIGS: dict[AgentType, AgentConfig] = {
    AgentType.PM: AgentConfig(
        type=AgentType.PM,
        name="Product Manager",
        description="Requirements gathering, task creation, prioritization",
        prompt_file="product-manager.md",
        model_tier=ModelTier.SONNET,
        capabilities=["requirements", "task_creation", "prioritization"],
    ),
    AgentType.ARCH: AgentConfig(
        type=AgentType.ARCH,
        name="Architect",
        description="System design, technology selection, API contracts",
        prompt_file="architect.md",
        model_tier=ModelTier.OPUS,
        capabilities=["system_design", "tech_selection", "api_design"],
    ),
    AgentType.RESEARCH: AgentConfig(
        type=AgentType.RESEARCH,
        name="Researcher",
        description="Investigation, analysis, best practices research",
        prompt_file="researcher.md",
        model_tier=ModelTier.SONNET,
        capabilities=["research", "analysis", "evaluation"],
    ),
    AgentType.GD: AgentConfig(
        type=AgentType.GD,
        name="Graphical Designer",
        description="Visual design, color schemes, typography, iconography",
        prompt_file="graphical-designer.md",
        model_tier=ModelTier.SONNET,
        capabilities=["visual_design", "branding", "graphics"],
    ),
    AgentType.UIUX: AgentConfig(
        type=AgentType.UIUX,
        name="UI/UX Specialist",
        description="User flows, wireframes, interaction design, accessibility",
        prompt_file="uiux-specialist.md",
        model_tier=ModelTier.SONNET,
        capabilities=["ux_design", "wireframes", "accessibility"],
    ),
    AgentType.CQR: AgentConfig(
        type=AgentType.CQR,
        name="Code Quality Reviewer",
        description="Code review, best practices, style compliance",
        prompt_file="code-quality-reviewer.md",
        model_tier=ModelTier.SONNET,
        capabilities=["code_review", "best_practices", "style"],
    ),
    AgentType.SR: AgentConfig(
        type=AgentType.SR,
        name="Security Reviewer",
        description="Security analysis, vulnerability detection, secure coding",
        prompt_file="security-reviewer.md",
        model_tier=ModelTier.OPUS,
        capabilities=["security_audit", "vulnerability_detection"],
    ),
    AgentType.QE: AgentConfig(
        type=AgentType.QE,
        name="Quality Engineer",
        description="Test planning, requirement validation, coverage analysis",
        prompt_file="quality-engineer.md",
        model_tier=ModelTier.SONNET,
        capabilities=["test_planning", "validation", "coverage"],
    ),
    AgentType.E2E: AgentConfig(
        type=AgentType.E2E,
        name="E2E Tester",
        description="End-to-end testing, integration testing, user journeys",
        prompt_file="e2e-tester.md",
        model_tier=ModelTier.SONNET,
        capabilities=["e2e_testing", "integration_testing"],
    ),
    AgentType.TQR: AgentConfig(
        type=AgentType.TQR,
        name="Task Quality Reviewer",
        description="Task clarity validation, specification completeness",
        prompt_file="task-quality-reviewer.md",
        model_tier=ModelTier.HAIKU,
        capabilities=["task_validation", "clarity_check"],
    ),
    AgentType.DOE: AgentConfig(
        type=AgentType.DOE,
        name="DevOps Engineer",
        description="CI/CD, infrastructure, deployment",
        prompt_file="devops-engineer.md",
        model_tier=ModelTier.SONNET,
        capabilities=["devops", "ci_cd", "infrastructure"],
    ),
    AgentType.TL_PYTHON: AgentConfig(
        type=AgentType.TL_PYTHON,
        name="Team Lead (Python)",
        description="Python team coordination, code standards, architecture decisions",
        prompt_file="team-lead.md",
        model_tier=ModelTier.SONNET,
        capabilities=["team_lead", "python", "coordination"],
    ),
    AgentType.TL_JAVASCRIPT: AgentConfig(
        type=AgentType.TL_JAVASCRIPT,
        name="Team Lead (JavaScript)",
        description="JavaScript team coordination, code standards, architecture decisions",
        prompt_file="team-lead.md",
        model_tier=ModelTier.SONNET,
        capabilities=["team_lead", "javascript", "coordination"],
    ),
    AgentType.DEV_PYTHON: AgentConfig(
        type=AgentType.DEV_PYTHON,
        name="Developer (Python)",
        description="Python implementation, coding, debugging",
        prompt_file="developer.md",
        model_tier=ModelTier.SONNET,
        capabilities=["development", "python", "implementation"],
    ),
    AgentType.DEV_JAVASCRIPT: AgentConfig(
        type=AgentType.DEV_JAVASCRIPT,
        name="Developer (JavaScript)",
        description="JavaScript implementation, coding, debugging",
        prompt_file="developer.md",
        model_tier=ModelTier.SONNET,
        capabilities=["development", "javascript", "implementation"],
    ),
}


def get_agent_config(agent_type: AgentType) -> AgentConfig | None:
    """Get configuration for an agent type.

    Args:
        agent_type: Agent type to look up

    Returns:
        AgentConfig or None if not found
    """
    return AGENT_CONFIGS.get(agent_type)


def get_all_agents() -> list[AgentConfig]:
    """Get all registered agents.

    Returns:
        List of all AgentConfig objects
    """
    return list(AGENT_CONFIGS.values())


def get_model_for_agent(agent_type: AgentType) -> ModelTier:
    """Get the model tier for an agent type.

    Args:
        agent_type: Agent type to look up

    Returns:
        ModelTier for the agent (defaults to SONNET)
    """
    config = get_agent_config(agent_type)
    return config.model_tier if config else ModelTier.SONNET
