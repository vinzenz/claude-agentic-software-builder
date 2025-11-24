"""Test configuration and fixtures."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from agentic_builder.storage.database import Database


@pytest.fixture
def temp_db_path(tmp_path):
    """Create a temporary database path for testing."""
    return tmp_path / "test.db"


@pytest.fixture(autouse=True)
def isolate_database(temp_db_path, request):
    """Isolate database for each test by using a temporary database."""
    # Skip database isolation for path-specific tests
    if request.cls and request.cls.__name__ == 'TestDatabasePath':
        yield
        return

    # Clear the global database instance
    from agentic_builder.storage import database
    database._db = None

    # Patch the Database.__init__ to use our temp path
    original_init = database.Database.__init__

    def patched_init(self, db_path=None):
        return original_init(self, temp_db_path)

    with patch.object(database.Database, '__init__', patched_init):
        # Create and initialize the database
        db = database.Database()
        db.initialize()
        # Set the global database instance
        database._db = db
        yield db
@pytest.fixture
def mock_project_dir(tmp_path):
    """Mock the project directory for testing."""
    project_dir = tmp_path / ".agentic"
    project_dir.mkdir()

    with patch('agentic_builder.core.config.get_project_dir', return_value=project_dir):
        yield project_dir


@pytest.fixture
def mock_env():
    """Mock environment variables for testing."""
    env_vars = {
        "AGENTIC_DEFAULT_MODEL": "sonnet",
        "AGENTIC_MAX_CONCURRENT_AGENTS": "3",
        "AGENTIC_TOKEN_BUDGET": "500000",
        "AGENTIC_LOG_LEVEL": "INFO",
        "AGENTIC_CLAUDE_CLI_PATH": "claude",
    }

    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def sample_workflow_data():
    """Sample workflow data for testing."""
    return {
        "workflow_id": "wf_20241124_120000_abc12345",
        "workflow_type": "full_project",
        "description": "Test project description",
    }


@pytest.fixture
def sample_task_data():
    """Sample task data for testing."""
    return {
        "task_id": "task_001",
        "workflow_id": "wf_20241124_120000_abc12345",
        "title": "Test Task",
        "agent_type": "PM",
        "description": "Test task description",
        "priority": "high",
        "stage_id": "stage_001",
        "created_by": "user",
    }


@pytest.fixture
def sample_agent_response():
    """Sample agent response XML for testing."""
    return """<task_output>
    <success>true</success>
    <summary>Task completed successfully</summary>
    <key_decisions>
    <decision>Use Python for implementation</decision>
    <decision>Follow TDD approach</decision>
    </key_decisions>
    <artifacts>
    <artifact type="code" name="main.py" description="Main application file">
    <content>def main():
    print("Hello, World!")</content>
    </artifact>
    </artifacts>
    <next_tasks>
    <task agent="DEV_PYTHON" priority="high">
    <title>Implement core functionality</title>
    <description>Implement the core business logic</description>
    <acceptance_criteria>
    <criterion>Code compiles without errors</criterion>
    <criterion>Basic functionality works</criterion>
    </acceptance_criteria>
    </task>
    </next_tasks>
    </task_output>"""


# Custom markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "database: marks tests that require database access"
    )