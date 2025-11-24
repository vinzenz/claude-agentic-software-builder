"""Configuration management."""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Config(BaseModel):
    """Application configuration."""

    default_model: str = os.getenv("AGENTIC_DEFAULT_MODEL", "sonnet")
    max_concurrent_agents: int = int(os.getenv("AGENTIC_MAX_CONCURRENT_AGENTS", "3"))
    token_budget: int = int(os.getenv("AGENTIC_TOKEN_BUDGET", "500000"))
    log_level: str = os.getenv("AGENTIC_LOG_LEVEL", "INFO")
    claude_cli_path: str = os.getenv("AGENTIC_CLAUDE_CLI_PATH", "claude")

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from environment."""
        return cls()


def get_project_dir() -> Path:
    """Get the .agentic directory for current project."""
    return Path.cwd() / ".agentic"


def get_db_path() -> Path:
    """Get the database path."""
    return get_project_dir() / "agentic.db"


def get_prompts_dir() -> Path:
    """Get the prompts directory (package-relative)."""
    return Path(__file__).parent.parent.parent.parent / "prompts" / "agents"


config = Config.load()
