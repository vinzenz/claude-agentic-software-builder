"""Tests for core configuration."""

import os
from pathlib import Path
from unittest.mock import patch


from agentic_builder.core.config import Config, get_db_path, get_project_dir, get_prompts_dir


class TestConfig:
    """Test configuration management."""

    def test_default_config(self):
        """Test default configuration values."""
        config = Config()
        assert config.default_model == "sonnet"
        assert config.max_concurrent_agents == 3
        assert config.token_budget == 500000
        assert config.log_level == "INFO"
        assert config.claude_cli_path == "claude"

    def test_config_from_env(self):
        """Test configuration loaded from environment variables."""
        env_vars = {
            "AGENTIC_DEFAULT_MODEL": "opus",
            "AGENTIC_MAX_CONCURRENT_AGENTS": "5",
            "AGENTIC_TOKEN_BUDGET": "1000000",
            "AGENTIC_LOG_LEVEL": "DEBUG",
            "AGENTIC_CLAUDE_CLI_PATH": "/custom/claude",
        }

        with patch.dict(os.environ, env_vars):
            config = Config()
            assert config.default_model == "opus"
            assert config.max_concurrent_agents == 5
            assert config.token_budget == 1000000
            assert config.log_level == "DEBUG"
            assert config.claude_cli_path == "/custom/claude"

    def test_load_method(self):
        """Test the load class method."""
        env_vars = {"AGENTIC_DEFAULT_MODEL": "haiku"}

        with patch.dict(os.environ, env_vars):
            config = Config()
            assert config.default_model == "haiku"


class TestPaths:
    """Test path utility functions."""

    def test_get_project_dir(self):
        """Test project directory path."""
        with patch("pathlib.Path.cwd", return_value=Path("/test/project")):
            project_dir = get_project_dir()
            assert project_dir == Path("/test/project/.agentic")

    def test_get_db_path(self):
        """Test database path."""
        with patch("pathlib.Path.cwd", return_value=Path("/test/project")):
            db_path = get_db_path()
            assert db_path == Path("/test/project/.agentic/agentic.db")

    def test_get_prompts_dir(self):
        """Test prompts directory path."""
        # This should point to the prompts directory in the package
        prompts_dir = get_prompts_dir()
        # The path should contain "prompts" and "agents"
        assert "prompts" in str(prompts_dir)
        assert "agents" in str(prompts_dir)
        assert prompts_dir.exists()  # Should exist in the actual project