"""Load agent prompts from files."""

from pathlib import Path

from agentic_builder.agents.registry import get_agent_config
from agentic_builder.core.config import get_prompts_dir
from agentic_builder.core.constants import AgentType

_prompt_cache: dict[AgentType, str] = {}


def load_prompt(agent_type: AgentType) -> str:
    """Load the system prompt for an agent type.

    Args:
        agent_type: Agent type to load prompt for

    Returns:
        System prompt string

    Raises:
        ValueError: If agent type is unknown
        FileNotFoundError: If prompt file doesn't exist
    """
    if agent_type in _prompt_cache:
        return _prompt_cache[agent_type]

    config = get_agent_config(agent_type)
    if not config:
        raise ValueError(f"Unknown agent type: {agent_type}")

    prompt_path = get_prompts_dir() / config.prompt_file
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    prompt = prompt_path.read_text()
    _prompt_cache[agent_type] = prompt
    return prompt


def clear_cache() -> None:
    """Clear the prompt cache."""
    _prompt_cache.clear()


def get_prompt_path(agent_type: AgentType) -> Path | None:
    """Get the path to an agent's prompt file.

    Args:
        agent_type: Agent type to look up

    Returns:
        Path to prompt file or None if agent not found
    """
    config = get_agent_config(agent_type)
    if not config:
        return None
    return get_prompts_dir() / config.prompt_file
