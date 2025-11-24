"""Tests for agent registry."""


from agentic_builder.agents.registry import (
    AGENT_CONFIGS,
    AgentConfig,
    get_agent_config,
    get_all_agents,
    get_model_for_agent,
)
from agentic_builder.core.constants import AgentType, ModelTier


class TestAgentConfig:
    """Test AgentConfig dataclass."""

    def test_agent_config_creation(self):
        """Test creating an AgentConfig instance."""
        config = AgentConfig(
            type=AgentType.PM,
            name="Product Manager",
            description="Requirements gathering",
            prompt_file="pm.md",
            model_tier=ModelTier.SONNET,
            capabilities=["requirements", "planning"],
        )

        assert config.type == AgentType.PM
        assert config.name == "Product Manager"
        assert config.description == "Requirements gathering"
        assert config.prompt_file == "pm.md"
        assert config.model_tier == ModelTier.SONNET
        assert config.capabilities == ["requirements", "planning"]


class TestAgentRegistry:
    """Test agent registry functions."""

    def test_get_agent_config_existing(self):
        """Test getting config for existing agent types."""
        config = get_agent_config(AgentType.PM)
        assert config is not None
        assert config.type == AgentType.PM
        assert config.name == "Product Manager"
        assert config.model_tier == ModelTier.SONNET

    def test_get_agent_config_nonexistent(self):
        """Test getting config for nonexistent agent type."""
        # Create a mock agent type that doesn't exist
        class MockAgentType:
            pass

        config = get_agent_config(MockAgentType())  # type: ignore
        assert config is None

    def test_get_all_agents(self):
        """Test getting all registered agents."""
        agents = get_all_agents()
        assert isinstance(agents, list)
        assert len(agents) > 0

        # Check that all agents are AgentConfig instances
        for agent in agents:
            assert isinstance(agent, AgentConfig)

        # Check that PM is in the list
        pm_configs = [a for a in agents if a.type == AgentType.PM]
        assert len(pm_configs) == 1

    def test_all_agent_configs_have_required_fields(self):
        """Test that all agent configs have required fields."""
        for agent_type, config in AGENT_CONFIGS.items():
            assert isinstance(config.type, AgentType)
            assert isinstance(config.name, str)
            assert len(config.name) > 0
            assert isinstance(config.description, str)
            assert len(config.description) > 0
            assert isinstance(config.prompt_file, str)
            assert len(config.prompt_file) > 0
            assert config.prompt_file.endswith(".md")
            assert isinstance(config.model_tier, ModelTier)
            assert isinstance(config.capabilities, list)
            assert len(config.capabilities) > 0

    def test_get_model_for_agent(self):
        """Test getting model tier for agent types."""
        # Test existing agent
        model = get_model_for_agent(AgentType.PM)
        assert model == ModelTier.SONNET

        # Test architect (should be opus)
        model = get_model_for_agent(AgentType.ARCH)
        assert model == ModelTier.OPUS

        # Test security reviewer (should be opus)
        model = get_model_for_agent(AgentType.SR)
        assert model == ModelTier.OPUS

        # Test task quality reviewer (should be haiku)
        model = get_model_for_agent(AgentType.TQR)
        assert model == ModelTier.HAIKU

    def test_get_model_for_unknown_agent(self):
        """Test getting model for unknown agent type (should default to sonnet)."""
        # Create a mock agent type
        class MockAgentType:
            pass

        model = get_model_for_agent(MockAgentType())  # type: ignore
        assert model == ModelTier.SONNET  # Default fallback

    def test_agent_config_uniqueness(self):
        """Test that each agent type has a unique configuration."""
        types = [config.type for config in AGENT_CONFIGS.values()]
        assert len(types) == len(set(types))  # No duplicates

    def test_prompt_files_exist(self):
        """Test that all referenced prompt files exist."""
        from agentic_builder.core.config import get_prompts_dir

        prompts_dir = get_prompts_dir()
        for config in AGENT_CONFIGS.values():
            prompt_path = prompts_dir / config.prompt_file
            assert prompt_path.exists(), f"Prompt file {config.prompt_file} does not exist"