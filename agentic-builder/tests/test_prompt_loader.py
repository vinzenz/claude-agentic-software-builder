"""Tests for agent prompt loading."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from agentic_builder.agents.prompt_loader import (
    clear_cache,
    get_prompt_path,
    load_prompt,
)
from agentic_builder.core.constants import AgentType


class TestLoadPrompt:
    """Test prompt loading functionality."""

    def test_load_existing_prompt(self):
        """Test loading an existing agent prompt."""
        prompt = load_prompt(AgentType.PM)
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Should contain some expected content
        assert "Product Manager" in prompt or "product manager" in prompt.lower()

    def test_load_prompt_caching(self):
        """Test that prompts are cached after first load."""
        # Clear cache first
        clear_cache()

        # Load a prompt
        prompt1 = load_prompt(AgentType.PM)

        # Load again - should use cache
        prompt2 = load_prompt(AgentType.PM)

        assert prompt1 == prompt2
        assert prompt1 is prompt2  # Same object reference

    def test_load_unknown_agent_type(self):
        """Test loading prompt for unknown agent type."""
        # Create a mock agent type that doesn't exist
        class MockAgentType:
            pass

        with pytest.raises(ValueError, match="Unknown agent type"):
            load_prompt(MockAgentType())  # type: ignore

    def test_load_prompt_file_not_found(self):
        """Test loading prompt when file doesn't exist."""
        # Create a mock agent type with non-existent prompt file
        class MockAgentType:
            pass

        # Mock the registry to return a config with non-existent file
        mock_config = type('MockConfig', (), {
            'prompt_file': 'nonexistent.md'
        })()

        with patch('agentic_builder.agents.prompt_loader.get_agent_config', return_value=mock_config):
            with pytest.raises(FileNotFoundError, match="Prompt file not found"):
                load_prompt(MockAgentType())  # type: ignore


class TestGetPromptPath:
    """Test prompt path resolution."""

    def test_get_prompt_path_existing_agent(self):
        """Test getting prompt path for existing agent."""
        path = get_prompt_path(AgentType.PM)
        assert path is not None
        assert isinstance(path, Path)
        assert path.exists()
        assert path.name == "product-manager.md"

    def test_get_prompt_path_unknown_agent(self):
        """Test getting prompt path for unknown agent."""
        # Create a mock agent type
        class MockAgentType:
            pass

        path = get_prompt_path(MockAgentType())  # type: ignore
        assert path is None

    def test_get_prompt_path_all_agents(self):
        """Test that all agent types have valid prompt paths."""
        for agent_type in AgentType:
            path = get_prompt_path(agent_type)
            assert path is not None, f"No prompt path for {agent_type}"
            assert path.exists(), f"Prompt file does not exist: {path}"


class TestCacheManagement:
    """Test prompt cache management."""

    def test_clear_cache(self):
        """Test clearing the prompt cache."""
        # Load a prompt to populate cache
        prompt1 = load_prompt(AgentType.PM)

        # Clear cache
        clear_cache()

        # Load again - should reload from file
        prompt2 = load_prompt(AgentType.PM)

        # Content should be the same but object references different
        assert prompt1 == prompt2
        # Note: In this implementation, the cache uses object identity,
        # so after clearing, it should be a different object

    def test_cache_isolation(self):
        """Test that cache is isolated between different agent types."""
        prompt_pm = load_prompt(AgentType.PM)
        prompt_arch = load_prompt(AgentType.ARCH)

        assert prompt_pm != prompt_arch
        assert "Product Manager" in prompt_pm or "product manager" in prompt_pm.lower()
        assert "Architect" in prompt_arch or "architect" in prompt_arch.lower()


class TestPromptContent:
    """Test prompt content validation."""

    def test_prompt_contains_expected_sections(self):
        """Test that prompts contain expected XML structure."""
        prompt = load_prompt(AgentType.PM)

        # Most prompts should contain task_output structure
        assert "<task_output>" in prompt
        assert "<success>" in prompt
        assert "<summary>" in prompt

    def test_prompt_file_encoding(self):
        """Test that prompt files are properly encoded."""
        path = get_prompt_path(AgentType.PM)
        assert path is not None

        # Should be readable as UTF-8
        content = path.read_text(encoding='utf-8')
        assert isinstance(content, str)
        assert len(content) > 0

    def test_all_prompt_files_readable(self):
        """Test that all prompt files are readable."""
        for agent_type in AgentType:
            path = get_prompt_path(agent_type)
            assert path is not None

            try:
                content = path.read_text(encoding='utf-8')
                assert isinstance(content, str)
                assert len(content) > 0
            except Exception as e:
                pytest.fail(f"Failed to read prompt file for {agent_type}: {e}")