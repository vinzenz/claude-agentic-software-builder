# Agentic Builder - Implementation Prompt

You are tasked with building `agentic-builder`, a Python CLI tool that orchestrates AI agents to build any software project. This prompt contains everything you need to implement the complete system.

## Overview

### What You're Building

A command-line tool called `agentic-builder` that:
1. Initializes in any directory to start a project
2. Accepts natural language project descriptions
3. Orchestrates multiple AI agents to design, implement, and test the project
4. Stores all state in SQLite for persistence and token efficiency
5. Uses XML-structured context passing to minimize token usage

### Success Criteria

When complete:
- [ ] `pip install -e .` succeeds
- [ ] `agentic-builder --help` shows all commands
- [ ] `agentic-builder init` creates `.agentic/` directory with database
- [ ] `agentic-builder start "Build a CLI todo app"` initiates a workflow
- [ ] Workflows execute agents in correct order with parallel execution where specified
- [ ] Token usage is tracked and budget limits enforced

### Tech Stack

- **Python 3.11+**
- **typer** - CLI framework
- **pydantic** - Data validation
- **rich** - Console output formatting
- **python-dotenv** - Environment configuration
- **sqlite3** - Built-in database (no external dependency)
- **Claude Code CLI** - Agent execution via `claude` in headless mode (external dependency)

---

## Section 1: Project Structure

Create the following directory structure:

```
agentic-builder/
├── pyproject.toml
├── README.md
├── .env.example
├── src/
│   └── agentic_builder/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── main.py
│       │   ├── commands/
│       │   │   ├── __init__.py
│       │   │   ├── init_cmd.py
│       │   │   ├── start.py
│       │   │   ├── status.py
│       │   │   ├── resume.py
│       │   │   ├── cancel.py
│       │   │   ├── logs.py
│       │   │   ├── agents.py
│       │   │   ├── tasks.py
│       │   │   └── usage.py
│       │   └── output.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py
│       │   ├── constants.py
│       │   └── exceptions.py
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── database.py
│       │   ├── schema.py
│       │   ├── tasks.py
│       │   └── workflows.py
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── registry.py
│       │   ├── executor.py
│       │   ├── prompt_loader.py
│       │   └── response_parser.py
│       ├── orchestration/
│       │   ├── __init__.py
│       │   ├── engine.py
│       │   ├── workflows.py
│       │   ├── stage_executor.py
│       │   └── model_selector.py
│       ├── context/
│       │   ├── __init__.py
│       │   ├── serializer.py
│       │   ├── windowing.py
│       │   └── budget.py
│       └── api/
│           ├── __init__.py
│           └── claude_cli.py
├── prompts/
│   └── agents/
│       ├── product-manager.md
│       ├── architect.md
│       ├── researcher.md
│       ├── graphical-designer.md
│       ├── uiux-specialist.md
│       ├── code-quality-reviewer.md
│       ├── security-reviewer.md
│       ├── quality-engineer.md
│       ├── e2e-tester.md
│       ├── task-quality-reviewer.md
│       ├── team-lead.md
│       ├── developer.md
│       └── devops-engineer.md
└── tests/
    └── __init__.py
```

### pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "agentic-builder"
version = "0.1.0"
description = "AI-powered software project builder using orchestrated agents"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "typer[all]>=0.9.0",
    "pydantic>=2.0.0",
    "python-dotenv>=1.0.0",
    "rich>=13.0.0",
]

[project.scripts]
agentic-builder = "agentic_builder.cli.main:app"

[tool.hatch.build.targets.wheel]
packages = ["src/agentic_builder"]
```

### src/agentic_builder/__init__.py

```python
"""Agentic Builder - AI-powered software project builder."""
__version__ = "0.1.0"
```

### src/agentic_builder/__main__.py

```python
"""Entry point for python -m agentic_builder."""
from agentic_builder.cli.main import app

if __name__ == "__main__":
    app()
```

### .env.example

```bash
# Optional configuration (Claude Code CLI handles authentication)
AGENTIC_DEFAULT_MODEL=sonnet
AGENTIC_MAX_CONCURRENT_AGENTS=3
AGENTIC_TOKEN_BUDGET=500000
AGENTIC_LOG_LEVEL=INFO
```

---

## Section 2: Core Module

### src/agentic_builder/core/constants.py

```python
"""Constants and enums for agentic-builder."""
from enum import Enum

class AgentType(str, Enum):
    """Agent type identifiers."""
    PM = "PM"
    ARCH = "ARCH"
    RESEARCH = "RESEARCH"
    GD = "GD"
    UIUX = "UIUX"
    CQR = "CQR"
    SR = "SR"
    QE = "QE"
    E2E = "E2E"
    TQR = "TQR"
    DOE = "DOE"
    # Dynamic types (created at runtime)
    TL_PYTHON = "TL_PYTHON"
    TL_JAVASCRIPT = "TL_JAVASCRIPT"
    DEV_PYTHON = "DEV_PYTHON"
    DEV_JAVASCRIPT = "DEV_JAVASCRIPT"

class ModelTier(str, Enum):
    """Claude model tiers."""
    HAIKU = "haiku"
    SONNET = "sonnet"
    OPUS = "opus"

class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

class StageStatus(str, Enum):
    """Stage execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

# Model mapping
AGENT_MODEL_TIERS: dict[AgentType, ModelTier] = {
    AgentType.PM: ModelTier.SONNET,
    AgentType.ARCH: ModelTier.OPUS,
    AgentType.RESEARCH: ModelTier.SONNET,
    AgentType.GD: ModelTier.SONNET,
    AgentType.UIUX: ModelTier.SONNET,
    AgentType.CQR: ModelTier.SONNET,
    AgentType.SR: ModelTier.OPUS,
    AgentType.QE: ModelTier.SONNET,
    AgentType.E2E: ModelTier.SONNET,
    AgentType.TQR: ModelTier.HAIKU,
    AgentType.DOE: ModelTier.SONNET,
}

# Token costs (per million tokens, 2025)
TOKEN_COSTS = {
    ModelTier.HAIKU: {"input": 0.25, "output": 1.25},
    ModelTier.SONNET: {"input": 3.0, "output": 15.0},
    ModelTier.OPUS: {"input": 15.0, "output": 75.0},
}

# Budget defaults
DEFAULT_WORKFLOW_BUDGET = 500_000
DEFAULT_AGENT_BUDGET = 50_000
BUDGET_WARNING_THRESHOLD = 0.8

# Context windowing
MAX_CHARS_PER_DEPENDENCY = 8000
MAX_TOTAL_CONTEXT_CHARS = 32000
SUMMARY_TARGET_CHARS = 1000
```

### src/agentic_builder/core/config.py

```python
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
    claude_cli_path: str = os.getenv("AGENTIC_CLAUDE_CLI_PATH", "claude")  # Path to claude CLI

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
```

### src/agentic_builder/core/exceptions.py

```python
"""Custom exceptions for agentic-builder."""

class AgenticError(Exception):
    """Base exception for agentic-builder."""
    pass

class NotInitializedError(AgenticError):
    """Project not initialized."""
    pass

class WorkflowNotFoundError(AgenticError):
    """Workflow not found."""
    pass

class TaskNotFoundError(AgenticError):
    """Task not found."""
    pass

class AgentExecutionError(AgenticError):
    """Agent execution failed."""
    pass

class TokenBudgetExceededError(AgenticError):
    """Token budget exceeded."""
    pass

class ConfigurationError(AgenticError):
    """Configuration error."""
    pass
```

---

## Section 3: Storage Layer

### src/agentic_builder/storage/schema.py

```python
"""SQLite schema definitions."""

SCHEMA_DDL = """
-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Workflow Runs
CREATE TABLE IF NOT EXISTS workflow_runs (
    id TEXT PRIMARY KEY,
    workflow_type TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    current_stage_id TEXT,
    total_tokens_used INTEGER DEFAULT 0,
    estimated_cost_usd REAL DEFAULT 0.0,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_workflow_runs_status ON workflow_runs(status);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_created ON workflow_runs(created_at DESC);

-- Workflow Stages
CREATE TABLE IF NOT EXISTS workflow_stages (
    id TEXT PRIMARY KEY,
    workflow_run_id TEXT NOT NULL,
    stage_name TEXT NOT NULL,
    stage_order INTEGER NOT NULL,
    parallel INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (workflow_run_id) REFERENCES workflow_runs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_workflow_stages_run ON workflow_stages(workflow_run_id);

-- Tasks
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    workflow_run_id TEXT NOT NULL,
    stage_id TEXT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    priority TEXT DEFAULT 'medium',
    agent_type TEXT NOT NULL,
    assigned_agent_instance_id TEXT,
    created_by TEXT,
    tokens_used INTEGER DEFAULT 0,
    execution_time_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (workflow_run_id) REFERENCES workflow_runs(id) ON DELETE CASCADE,
    FOREIGN KEY (stage_id) REFERENCES workflow_stages(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_tasks_workflow ON tasks(workflow_run_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_agent ON tasks(agent_type);

-- Task Dependencies
CREATE TABLE IF NOT EXISTS task_dependencies (
    task_id TEXT NOT NULL,
    depends_on_task_id TEXT NOT NULL,
    dependency_type TEXT DEFAULT 'required',
    PRIMARY KEY (task_id, depends_on_task_id),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- Task Context
CREATE TABLE IF NOT EXISTS task_context (
    task_id TEXT PRIMARY KEY,
    context_xml TEXT NOT NULL,
    context_tokens INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- Task Outputs
CREATE TABLE IF NOT EXISTS task_outputs (
    task_id TEXT PRIMARY KEY,
    output_xml TEXT NOT NULL,
    summary TEXT,
    key_decisions TEXT,
    artifacts TEXT,
    tokens_used INTEGER,
    model_used TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- Agent Instances
CREATE TABLE IF NOT EXISTS agent_instances (
    id TEXT PRIMARY KEY,
    agent_type TEXT NOT NULL,
    workflow_run_id TEXT NOT NULL,
    task_id TEXT,
    status TEXT NOT NULL DEFAULT 'idle',
    model_tier TEXT DEFAULT 'sonnet',
    tokens_used INTEGER DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    FOREIGN KEY (workflow_run_id) REFERENCES workflow_runs(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_agent_instances_workflow ON agent_instances(workflow_run_id);

-- Artifacts
CREATE TABLE IF NOT EXISTS artifacts (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    workflow_run_id TEXT NOT NULL,
    name TEXT NOT NULL,
    artifact_type TEXT NOT NULL,
    file_path TEXT,
    content TEXT,
    language TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (workflow_run_id) REFERENCES workflow_runs(id) ON DELETE CASCADE
);

-- Token Usage Log
CREATE TABLE IF NOT EXISTS token_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_run_id TEXT NOT NULL,
    task_id TEXT,
    agent_type TEXT,
    model TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cost_usd REAL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workflow_run_id) REFERENCES workflow_runs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_token_usage_workflow ON token_usage(workflow_run_id);

-- Configuration
CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Default configuration
INSERT OR IGNORE INTO config (key, value) VALUES
    ('project_name', ''),
    ('default_model_tier', 'sonnet'),
    ('max_tokens_per_workflow', '500000'),
    ('max_tokens_per_agent', '50000'),
    ('auto_resume_enabled', 'true');
"""
```

### src/agentic_builder/storage/database.py

```python
"""SQLite database connection management."""
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

from agentic_builder.core.config import get_db_path
from agentic_builder.storage.schema import SCHEMA_DDL

class Database:
    """SQLite database manager."""

    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or get_db_path()
        self._connection: sqlite3.Connection | None = None

    def initialize(self) -> None:
        """Initialize database with schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as conn:
            conn.executescript(SCHEMA_DDL)

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute(self, query: str, params: tuple = ()) -> list[sqlite3.Row]:
        """Execute a query and return results."""
        with self.connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()

    def execute_one(self, query: str, params: tuple = ()) -> sqlite3.Row | None:
        """Execute a query and return single result."""
        with self.connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchone()

    def execute_write(self, query: str, params: tuple = ()) -> int:
        """Execute a write query and return rows affected."""
        with self.connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.rowcount

# Global database instance (lazy init)
_db: Database | None = None

def get_db() -> Database:
    """Get the global database instance."""
    global _db
    if _db is None:
        _db = Database()
    return _db
```

### src/agentic_builder/storage/tasks.py

```python
"""Task storage operations."""
import json
from datetime import datetime
from typing import Optional
from agentic_builder.storage.database import get_db
from agentic_builder.core.constants import TaskStatus

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
    """Create a new task."""
    db = get_db()
    db.execute_write(
        """
        INSERT INTO tasks (id, workflow_run_id, stage_id, title, description,
                          status, priority, agent_type, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (task_id, workflow_run_id, stage_id, title, description,
         TaskStatus.PENDING.value, priority, agent_type, created_by)
    )

def get_task(task_id: str) -> dict | None:
    """Get task by ID."""
    db = get_db()
    row = db.execute_one("SELECT * FROM tasks WHERE id = ?", (task_id,))
    return dict(row) if row else None

def get_workflow_tasks(workflow_run_id: str, status: str | None = None) -> list[dict]:
    """Get tasks for a workflow."""
    db = get_db()
    if status:
        rows = db.execute(
            "SELECT * FROM tasks WHERE workflow_run_id = ? AND status = ? ORDER BY created_at",
            (workflow_run_id, status)
        )
    else:
        rows = db.execute(
            "SELECT * FROM tasks WHERE workflow_run_id = ? ORDER BY created_at",
            (workflow_run_id,)
        )
    return [dict(row) for row in rows]

def update_task_status(task_id: str, status: TaskStatus, error_message: str | None = None) -> None:
    """Update task status."""
    db = get_db()
    now = datetime.utcnow().isoformat()
    if status == TaskStatus.COMPLETED:
        db.execute_write(
            "UPDATE tasks SET status = ?, completed_at = ?, updated_at = ? WHERE id = ?",
            (status.value, now, now, task_id)
        )
    elif error_message:
        db.execute_write(
            "UPDATE tasks SET status = ?, error_message = ?, updated_at = ? WHERE id = ?",
            (status.value, error_message, now, task_id)
        )
    else:
        db.execute_write(
            "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
            (status.value, now, task_id)
        )

def add_task_dependency(task_id: str, depends_on_task_id: str) -> None:
    """Add a dependency between tasks."""
    db = get_db()
    db.execute_write(
        "INSERT OR IGNORE INTO task_dependencies (task_id, depends_on_task_id) VALUES (?, ?)",
        (task_id, depends_on_task_id)
    )

def get_task_dependencies(task_id: str) -> list[str]:
    """Get task IDs this task depends on."""
    db = get_db()
    rows = db.execute(
        "SELECT depends_on_task_id FROM task_dependencies WHERE task_id = ?",
        (task_id,)
    )
    return [row["depends_on_task_id"] for row in rows]

def get_runnable_tasks(workflow_run_id: str) -> list[dict]:
    """Get tasks that are ready to run (all dependencies completed)."""
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
        (workflow_run_id,)
    )
    return [dict(row) for row in rows]

def save_task_context(task_id: str, context_xml: str, token_count: int) -> None:
    """Save task context."""
    db = get_db()
    db.execute_write(
        """
        INSERT OR REPLACE INTO task_context (task_id, context_xml, context_tokens)
        VALUES (?, ?, ?)
        """,
        (task_id, context_xml, token_count)
    )

def get_task_context(task_id: str) -> str | None:
    """Get task context XML."""
    db = get_db()
    row = db.execute_one("SELECT context_xml FROM task_context WHERE task_id = ?", (task_id,))
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
    """Save task output."""
    db = get_db()
    db.execute_write(
        """
        INSERT OR REPLACE INTO task_outputs
        (task_id, output_xml, summary, key_decisions, artifacts, tokens_used, model_used)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (task_id, output_xml, summary, json.dumps(key_decisions),
         json.dumps(artifacts), tokens_used, model_used)
    )

def get_task_output(task_id: str) -> dict | None:
    """Get task output."""
    db = get_db()
    row = db.execute_one("SELECT * FROM task_outputs WHERE task_id = ?", (task_id,))
    if row:
        result = dict(row)
        result["key_decisions"] = json.loads(result["key_decisions"] or "[]")
        result["artifacts"] = json.loads(result["artifacts"] or "[]")
        return result
    return None
```

### src/agentic_builder/storage/workflows.py

```python
"""Workflow storage operations."""
import uuid
from datetime import datetime
from agentic_builder.storage.database import get_db
from agentic_builder.core.constants import WorkflowStatus, StageStatus

def generate_workflow_id() -> str:
    """Generate a unique workflow ID."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    short_uuid = uuid.uuid4().hex[:8]
    return f"wf_{timestamp}_{short_uuid}"

def create_workflow(
    workflow_type: str,
    description: str,
) -> str:
    """Create a new workflow run."""
    db = get_db()
    workflow_id = generate_workflow_id()
    db.execute_write(
        """
        INSERT INTO workflow_runs (id, workflow_type, description, status)
        VALUES (?, ?, ?, ?)
        """,
        (workflow_id, workflow_type, description, WorkflowStatus.PENDING.value)
    )
    return workflow_id

def get_workflow(workflow_id: str) -> dict | None:
    """Get workflow by ID."""
    db = get_db()
    row = db.execute_one("SELECT * FROM workflow_runs WHERE id = ?", (workflow_id,))
    return dict(row) if row else None

def get_latest_workflow() -> dict | None:
    """Get the most recent workflow."""
    db = get_db()
    row = db.execute_one(
        "SELECT * FROM workflow_runs ORDER BY created_at DESC LIMIT 1"
    )
    return dict(row) if row else None

def get_workflows(status: str | None = None, limit: int = 20) -> list[dict]:
    """Get workflows with optional status filter."""
    db = get_db()
    if status:
        rows = db.execute(
            "SELECT * FROM workflow_runs WHERE status = ? ORDER BY created_at DESC LIMIT ?",
            (status, limit)
        )
    else:
        rows = db.execute(
            "SELECT * FROM workflow_runs ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
    return [dict(row) for row in rows]

def update_workflow_status(
    workflow_id: str,
    status: WorkflowStatus,
    error_message: str | None = None
) -> None:
    """Update workflow status."""
    db = get_db()
    now = datetime.utcnow().isoformat()
    if status == WorkflowStatus.RUNNING:
        db.execute_write(
            "UPDATE workflow_runs SET status = ?, started_at = ?, updated_at = ? WHERE id = ?",
            (status.value, now, now, workflow_id)
        )
    elif status == WorkflowStatus.COMPLETED:
        db.execute_write(
            "UPDATE workflow_runs SET status = ?, completed_at = ?, updated_at = ? WHERE id = ?",
            (status.value, now, now, workflow_id)
        )
    elif error_message:
        db.execute_write(
            "UPDATE workflow_runs SET status = ?, error_message = ?, updated_at = ? WHERE id = ?",
            (status.value, error_message, now, workflow_id)
        )
    else:
        db.execute_write(
            "UPDATE workflow_runs SET status = ?, updated_at = ? WHERE id = ?",
            (status.value, now, workflow_id)
        )

def add_tokens_to_workflow(workflow_id: str, tokens: int, cost: float) -> None:
    """Add token usage to workflow total."""
    db = get_db()
    db.execute_write(
        """
        UPDATE workflow_runs
        SET total_tokens_used = total_tokens_used + ?,
            estimated_cost_usd = estimated_cost_usd + ?,
            updated_at = ?
        WHERE id = ?
        """,
        (tokens, cost, datetime.utcnow().isoformat(), workflow_id)
    )

def create_stage(
    workflow_run_id: str,
    stage_name: str,
    stage_order: int,
    parallel: bool = False,
) -> str:
    """Create a workflow stage."""
    db = get_db()
    stage_id = f"{workflow_run_id}_stage_{stage_order:02d}"
    db.execute_write(
        """
        INSERT INTO workflow_stages (id, workflow_run_id, stage_name, stage_order, parallel, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (stage_id, workflow_run_id, stage_name, stage_order, int(parallel), StageStatus.PENDING.value)
    )
    return stage_id

def get_workflow_stages(workflow_run_id: str) -> list[dict]:
    """Get stages for a workflow."""
    db = get_db()
    rows = db.execute(
        "SELECT * FROM workflow_stages WHERE workflow_run_id = ? ORDER BY stage_order",
        (workflow_run_id,)
    )
    return [dict(row) for row in rows]

def update_stage_status(stage_id: str, status: StageStatus) -> None:
    """Update stage status."""
    db = get_db()
    now = datetime.utcnow().isoformat()
    if status == StageStatus.RUNNING:
        db.execute_write(
            "UPDATE workflow_stages SET status = ?, started_at = ? WHERE id = ?",
            (status.value, now, stage_id)
        )
    elif status in (StageStatus.COMPLETED, StageStatus.FAILED, StageStatus.SKIPPED):
        db.execute_write(
            "UPDATE workflow_stages SET status = ?, completed_at = ? WHERE id = ?",
            (status.value, now, stage_id)
        )
    else:
        db.execute_write(
            "UPDATE workflow_stages SET status = ? WHERE id = ?",
            (status.value, stage_id)
        )
```

---

## Section 4: Context Management

### src/agentic_builder/context/serializer.py

```python
"""XML context serialization for agent communication."""
import xml.etree.ElementTree as ET
from typing import Any

def escape_xml(text: str) -> str:
    """Escape XML special characters."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;"))

def dict_to_xml(data: dict, root_tag: str = "data") -> str:
    """Convert dictionary to XML string."""
    root = ET.Element(root_tag)
    _add_dict_to_element(root, data)
    return ET.tostring(root, encoding="unicode")

def _add_dict_to_element(parent: ET.Element, data: dict) -> None:
    """Recursively add dictionary to XML element."""
    for key, value in data.items():
        tag = key.replace(" ", "_").replace("-", "_")
        if isinstance(value, dict):
            child = ET.SubElement(parent, tag)
            _add_dict_to_element(child, value)
        elif isinstance(value, list):
            child = ET.SubElement(parent, tag)
            for item in value:
                if isinstance(item, dict):
                    item_elem = ET.SubElement(child, "item")
                    _add_dict_to_element(item_elem, item)
                else:
                    item_elem = ET.SubElement(child, "item")
                    item_elem.text = str(item)
        elif value is not None:
            child = ET.SubElement(parent, tag)
            child.text = str(value)

def build_task_context(
    task_id: str,
    agent_type: str,
    workflow_id: str,
    summary: str,
    requirements: list[str],
    constraints: list[str],
    dependencies: list[dict],
    artifacts: list[dict],
    acceptance_criteria: list[str],
) -> str:
    """Build the XML context for a task."""
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append("<task_input>")

    # Meta section
    lines.append("  <meta>")
    lines.append(f"    <task_id>{escape_xml(task_id)}</task_id>")
    lines.append(f"    <agent_type>{escape_xml(agent_type)}</agent_type>")
    lines.append(f"    <workflow_id>{escape_xml(workflow_id)}</workflow_id>")
    lines.append("  </meta>")

    # Summary
    lines.append(f"  <summary>{escape_xml(summary)}</summary>")

    # Requirements
    if requirements:
        lines.append("  <requirements>")
        for req in requirements:
            lines.append(f"    <requirement>{escape_xml(req)}</requirement>")
        lines.append("  </requirements>")

    # Constraints
    if constraints:
        lines.append("  <constraints>")
        for con in constraints:
            lines.append(f"    <constraint>{escape_xml(con)}</constraint>")
        lines.append("  </constraints>")

    # Dependencies
    if dependencies:
        lines.append("  <dependencies>")
        for dep in dependencies:
            lines.append(f'    <dependency task_id="{escape_xml(dep["task_id"])}" agent="{escape_xml(dep["agent_type"])}">')
            lines.append(f"      <summary>{escape_xml(dep.get('summary', ''))}</summary>")
            if dep.get("key_decisions"):
                lines.append("      <key_decisions>")
                for dec in dep["key_decisions"]:
                    lines.append(f"        <decision>{escape_xml(dec)}</decision>")
                lines.append("      </key_decisions>")
            lines.append("    </dependency>")
        lines.append("  </dependencies>")

    # Existing artifacts
    if artifacts:
        lines.append("  <existing_artifacts>")
        for art in artifacts:
            lines.append(f'    <artifact type="{escape_xml(art["type"])}" path="{escape_xml(art.get("path", ""))}">')
            lines.append(f"      {escape_xml(art.get('description', ''))}")
            lines.append("    </artifact>")
        lines.append("  </existing_artifacts>")

    # Acceptance criteria
    if acceptance_criteria:
        lines.append("  <acceptance_criteria>")
        for crit in acceptance_criteria:
            lines.append(f"    <criterion>{escape_xml(crit)}</criterion>")
        lines.append("  </acceptance_criteria>")

    lines.append("</task_input>")
    return "\n".join(lines)
```

### src/agentic_builder/context/windowing.py

```python
"""Context windowing for token efficiency."""
from agentic_builder.core.constants import (
    MAX_CHARS_PER_DEPENDENCY,
    MAX_TOTAL_CONTEXT_CHARS,
    SUMMARY_TARGET_CHARS,
)

def estimate_tokens(text: str) -> int:
    """Estimate token count from text (roughly 4 chars per token)."""
    return len(text) // 4

def truncate_to_summary(text: str, target_chars: int = SUMMARY_TARGET_CHARS) -> str:
    """Truncate text to summary length."""
    if len(text) <= target_chars:
        return text
    # Try to cut at sentence boundary
    truncated = text[:target_chars]
    last_period = truncated.rfind(".")
    if last_period > target_chars // 2:
        return truncated[:last_period + 1]
    return truncated + "..."

def apply_windowing(dependencies: list[dict]) -> list[dict]:
    """Apply windowing to dependency outputs for token efficiency."""
    total_chars = 0
    windowed = []

    for dep in dependencies:
        output = dep.get("output", "")

        # Window individual dependency
        if len(output) > MAX_CHARS_PER_DEPENDENCY:
            output = truncate_to_summary(output, MAX_CHARS_PER_DEPENDENCY)

        # Check total budget
        if total_chars + len(output) > MAX_TOTAL_CONTEXT_CHARS:
            # Further truncate to fit
            remaining = MAX_TOTAL_CONTEXT_CHARS - total_chars
            if remaining > SUMMARY_TARGET_CHARS:
                output = truncate_to_summary(output, remaining)
            else:
                # Skip this dependency, budget exhausted
                continue

        windowed.append({**dep, "output": output})
        total_chars += len(output)

    return windowed
```

### src/agentic_builder/context/budget.py

```python
"""Token budget tracking."""
from agentic_builder.storage.database import get_db
from agentic_builder.core.constants import (
    TOKEN_COSTS,
    ModelTier,
    DEFAULT_WORKFLOW_BUDGET,
    BUDGET_WARNING_THRESHOLD,
)

def calculate_cost(model_tier: ModelTier, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost in USD for token usage."""
    costs = TOKEN_COSTS[model_tier]
    input_cost = (input_tokens / 1_000_000) * costs["input"]
    output_cost = (output_tokens / 1_000_000) * costs["output"]
    return input_cost + output_cost

def record_usage(
    workflow_run_id: str,
    task_id: str,
    agent_type: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """Record token usage and return cost."""
    model_tier = ModelTier(model.split("-")[1] if "-" in model else model)
    cost = calculate_cost(model_tier, input_tokens, output_tokens)

    db = get_db()
    db.execute_write(
        """
        INSERT INTO token_usage (workflow_run_id, task_id, agent_type, model, input_tokens, output_tokens, cost_usd)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (workflow_run_id, task_id, agent_type, model, input_tokens, output_tokens, cost)
    )
    return cost

def get_workflow_usage(workflow_run_id: str) -> dict:
    """Get token usage summary for a workflow."""
    db = get_db()
    row = db.execute_one(
        """
        SELECT
            SUM(input_tokens) as total_input,
            SUM(output_tokens) as total_output,
            SUM(cost_usd) as total_cost
        FROM token_usage
        WHERE workflow_run_id = ?
        """,
        (workflow_run_id,)
    )
    return {
        "total_input": row["total_input"] or 0,
        "total_output": row["total_output"] or 0,
        "total_tokens": (row["total_input"] or 0) + (row["total_output"] or 0),
        "total_cost": row["total_cost"] or 0.0,
    }

def check_budget(workflow_run_id: str, budget: int = DEFAULT_WORKFLOW_BUDGET) -> tuple[bool, float]:
    """Check if workflow is within budget. Returns (within_budget, usage_percent)."""
    usage = get_workflow_usage(workflow_run_id)
    total = usage["total_tokens"]
    percent = total / budget if budget > 0 else 0
    return total < budget, percent

def is_budget_warning(workflow_run_id: str, budget: int = DEFAULT_WORKFLOW_BUDGET) -> bool:
    """Check if budget warning threshold reached."""
    within_budget, percent = check_budget(workflow_run_id, budget)
    return percent >= BUDGET_WARNING_THRESHOLD
```

---

## Section 5: Agent System

### src/agentic_builder/agents/registry.py

```python
"""Agent type registry and configuration."""
from dataclasses import dataclass
from agentic_builder.core.constants import AgentType, ModelTier, AGENT_MODEL_TIERS

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
}

def get_agent_config(agent_type: AgentType) -> AgentConfig:
    """Get configuration for an agent type."""
    return AGENT_CONFIGS.get(agent_type)

def get_all_agents() -> list[AgentConfig]:
    """Get all registered agents."""
    return list(AGENT_CONFIGS.values())

def get_model_for_agent(agent_type: AgentType) -> ModelTier:
    """Get the model tier for an agent type."""
    config = get_agent_config(agent_type)
    return config.model_tier if config else ModelTier.SONNET
```

### src/agentic_builder/agents/prompt_loader.py

```python
"""Load agent prompts from files."""
from pathlib import Path
from agentic_builder.core.config import get_prompts_dir
from agentic_builder.agents.registry import get_agent_config
from agentic_builder.core.constants import AgentType

_prompt_cache: dict[AgentType, str] = {}

def load_prompt(agent_type: AgentType) -> str:
    """Load the system prompt for an agent type."""
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
```

### src/agentic_builder/agents/response_parser.py

```python
"""Parse agent XML responses."""
import re
import json
from dataclasses import dataclass, field

@dataclass
class AgentResponse:
    """Parsed agent response."""
    success: bool
    summary: str
    key_decisions: list[str] = field(default_factory=list)
    artifacts: list[dict] = field(default_factory=list)
    next_tasks: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    raw_xml: str = ""

def extract_tag_content(xml: str, tag: str) -> str | None:
    """Extract content from an XML tag."""
    pattern = rf"<{tag}[^>]*>(.*?)</{tag}>"
    match = re.search(pattern, xml, re.DOTALL)
    return match.group(1).strip() if match else None

def extract_list_items(xml: str, container_tag: str, item_tag: str) -> list[str]:
    """Extract list of items from XML."""
    container = extract_tag_content(xml, container_tag)
    if not container:
        return []
    pattern = rf"<{item_tag}[^>]*>(.*?)</{item_tag}>"
    matches = re.findall(pattern, container, re.DOTALL)
    return [m.strip() for m in matches]

def parse_response(xml: str) -> AgentResponse:
    """Parse agent XML response into structured data."""
    # Find task_output block
    output_xml = extract_tag_content(xml, "task_output")
    if not output_xml:
        # Try to find it in the raw response
        if "<task_output>" in xml:
            start = xml.index("<task_output>")
            end = xml.index("</task_output>") + len("</task_output>")
            output_xml = xml[start:end]
        else:
            return AgentResponse(
                success=False,
                summary="Failed to parse response - no task_output found",
                raw_xml=xml,
            )

    # Extract fields
    success_str = extract_tag_content(output_xml, "success")
    success = success_str.lower() == "true" if success_str else False

    summary = extract_tag_content(output_xml, "summary") or ""
    key_decisions = extract_list_items(output_xml, "key_decisions", "decision")
    warnings = extract_list_items(output_xml, "warnings", "warning")

    # Parse artifacts
    artifacts = []
    artifacts_xml = extract_tag_content(output_xml, "artifacts")
    if artifacts_xml:
        artifact_pattern = r'<artifact\s+type="([^"]+)"\s+name="([^"]+)"[^>]*>(.*?)</artifact>'
        for match in re.finditer(artifact_pattern, artifacts_xml, re.DOTALL):
            art_type, art_name, art_content = match.groups()
            description = extract_tag_content(art_content, "description") or ""
            content = extract_tag_content(art_content, "content") or ""
            artifacts.append({
                "type": art_type,
                "name": art_name,
                "description": description,
                "content": content,
            })

    # Parse next_tasks
    next_tasks = []
    tasks_xml = extract_tag_content(output_xml, "next_tasks")
    if tasks_xml:
        task_pattern = r'<task\s+agent="([^"]+)"\s+priority="([^"]+)"[^>]*>(.*?)</task>'
        for match in re.finditer(task_pattern, tasks_xml, re.DOTALL):
            agent, priority, task_content = match.groups()
            title = extract_tag_content(task_content, "title") or ""
            description = extract_tag_content(task_content, "description") or ""
            criteria = extract_list_items(task_content, "acceptance_criteria", "criterion")
            next_tasks.append({
                "agent_type": agent,
                "priority": priority,
                "title": title,
                "description": description,
                "acceptance_criteria": criteria,
            })

    return AgentResponse(
        success=success,
        summary=summary,
        key_decisions=key_decisions,
        artifacts=artifacts,
        next_tasks=next_tasks,
        warnings=warnings,
        raw_xml=xml,
    )
```

### src/agentic_builder/agents/executor.py

```python
"""Agent execution logic."""
import asyncio
from datetime import datetime
from agentic_builder.api.claude_cli import ClaudeCLI
from agentic_builder.agents.prompt_loader import load_prompt
from agentic_builder.agents.response_parser import parse_response, AgentResponse
from agentic_builder.agents.registry import get_model_for_agent
from agentic_builder.storage import tasks as task_storage
from agentic_builder.context.budget import record_usage
from agentic_builder.core.constants import AgentType, TaskStatus, ModelTier

# Model aliases for Claude Code CLI
MODEL_ALIASES = {
    ModelTier.HAIKU: "haiku",
    ModelTier.SONNET: "sonnet",
    ModelTier.OPUS: "opus",
}

async def execute_agent(
    task_id: str,
    agent_type: AgentType,
    workflow_run_id: str,
    context_xml: str,
) -> AgentResponse:
    """Execute an agent for a task using Claude Code CLI in headless mode."""
    # Update task status
    task_storage.update_task_status(task_id, TaskStatus.RUNNING)

    try:
        # Load prompt
        system_prompt = load_prompt(agent_type)

        # Get model alias
        model_tier = get_model_for_agent(agent_type)
        model_alias = MODEL_ALIASES[model_tier]

        # Build user message
        user_message = f"""Please complete the following task.

{context_xml}

Respond with your output in the XML format specified in your system prompt."""

        # Call Claude CLI in headless mode
        cli = ClaudeCLI()
        start_time = datetime.utcnow()

        result = await cli.execute(
            prompt=user_message,
            system_prompt=system_prompt,
            model=model_alias,
            max_turns=1,  # Single turn for agent execution
        )

        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Extract token usage from CLI response
        input_tokens = result.get("input_tokens", 0)
        output_tokens = result.get("output_tokens", 0)
        total_cost = result.get("total_cost_usd", 0.0)

        # Record token usage
        record_usage(
            workflow_run_id=workflow_run_id,
            task_id=task_id,
            agent_type=agent_type.value,
            model=model_alias,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        # Parse response
        response_text = result.get("result", "")
        parsed = parse_response(response_text)

        # Save output
        task_storage.save_task_output(
            task_id=task_id,
            output_xml=response_text,
            summary=parsed.summary,
            key_decisions=parsed.key_decisions,
            artifacts=parsed.artifacts,
            tokens_used=input_tokens + output_tokens,
            model_used=model_alias,
        )

        # Update task status
        if parsed.success:
            task_storage.update_task_status(task_id, TaskStatus.COMPLETED)
        else:
            task_storage.update_task_status(
                task_id, TaskStatus.FAILED, error_message=parsed.summary
            )

        return parsed

    except Exception as e:
        task_storage.update_task_status(
            task_id, TaskStatus.FAILED, error_message=str(e)
        )
        raise
```

---

## Section 6: Claude CLI Client

### src/agentic_builder/api/claude_cli.py

```python
"""Claude Code CLI wrapper for headless agent execution.

This module uses the Claude Code CLI in headless mode (--print flag) instead of
the Anthropic API directly. This approach:
- Uses Claude Code's authentication (no API key management needed)
- Provides JSON-structured output with token usage and cost tracking
- Supports model selection via simple aliases (haiku, sonnet, opus)

Reference: https://code.claude.com/docs/en/headless
CLI Reference: https://code.claude.com/docs/en/cli-reference
"""
import asyncio
import json
import subprocess
import tempfile
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from agentic_builder.core.config import config
from agentic_builder.core.exceptions import AgentExecutionError

@dataclass
class CLIResult:
    """Result from Claude CLI execution."""
    success: bool
    result: str
    session_id: str
    input_tokens: int
    output_tokens: int
    total_cost_usd: float
    duration_ms: int
    error: Optional[str] = None

class ClaudeCLI:
    """Claude Code CLI wrapper for headless execution.

    Uses `claude -p` (print mode) with JSON output for programmatic execution.
    """

    def __init__(self, cli_path: str | None = None):
        """Initialize CLI wrapper.

        Args:
            cli_path: Path to claude CLI executable. Defaults to 'claude'.
        """
        self.cli_path = cli_path or config.claude_cli_path

    async def execute(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str = "sonnet",
        max_turns: int = 1,
        allowed_tools: list[str] | None = None,
        session_id: str | None = None,
    ) -> dict:
        """Execute Claude in headless mode.

        Args:
            prompt: The user prompt to send.
            system_prompt: Custom system prompt (appended to default).
            model: Model alias (haiku, sonnet, opus).
            max_turns: Maximum agentic turns (default 1 for single response).
            allowed_tools: List of tools to allow (restricts tool access).
            session_id: Resume a previous session.

        Returns:
            dict with keys: result, session_id, input_tokens, output_tokens,
                           total_cost_usd, duration_ms

        Raises:
            AgentExecutionError: If CLI execution fails.
        """
        # Build command
        cmd = [
            self.cli_path,
            "--print",  # Headless mode
            "--output-format", "json",  # JSON output for parsing
            "--model", model,
            "--max-turns", str(max_turns),
        ]

        # Add system prompt if provided
        if system_prompt:
            # Write system prompt to temp file for --append-system-prompt
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                f.write(system_prompt)
                system_prompt_file = f.name
            cmd.extend(["--system-prompt-file", system_prompt_file])

        # Add tool restrictions if specified
        if allowed_tools:
            cmd.extend(["--allowedTools", ",".join(allowed_tools)])

        # Add session resumption if specified
        if session_id:
            cmd.extend(["--resume", session_id])

        # Add the prompt as the final argument
        cmd.append(prompt)

        try:
            # Run CLI command asynchronously
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise AgentExecutionError(f"Claude CLI failed: {error_msg}")

            # Parse JSON output
            output = stdout.decode()

            # Claude CLI outputs multiple JSON objects for streaming, get the final result
            # The last line with type "result" contains the final response
            result_data = None
            for line in output.strip().split("\n"):
                if line.strip():
                    try:
                        data = json.loads(line)
                        if data.get("type") == "result":
                            result_data = data
                    except json.JSONDecodeError:
                        continue

            if not result_data:
                # Try parsing the entire output as single JSON
                try:
                    result_data = json.loads(output)
                except json.JSONDecodeError:
                    # Fallback: treat output as plain text response
                    return {
                        "result": output,
                        "session_id": "",
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "total_cost_usd": 0.0,
                        "duration_ms": 0,
                    }

            return {
                "result": result_data.get("result", ""),
                "session_id": result_data.get("session_id", ""),
                "input_tokens": result_data.get("input_tokens", 0),
                "output_tokens": result_data.get("output_tokens", 0),
                "total_cost_usd": result_data.get("total_cost_usd", 0.0),
                "duration_ms": result_data.get("duration_ms", 0),
            }

        except asyncio.CancelledError:
            raise
        except AgentExecutionError:
            raise
        except Exception as e:
            raise AgentExecutionError(f"Failed to execute Claude CLI: {e}")
        finally:
            # Clean up temp file if created
            if system_prompt and 'system_prompt_file' in locals():
                try:
                    Path(system_prompt_file).unlink()
                except:
                    pass

    async def resume_session(
        self,
        session_id: str,
        prompt: str,
        model: str = "sonnet",
    ) -> dict:
        """Resume a previous conversation session.

        Args:
            session_id: The session ID to resume.
            prompt: The follow-up prompt.
            model: Model alias.

        Returns:
            dict with response data.
        """
        return await self.execute(
            prompt=prompt,
            model=model,
            session_id=session_id,
        )

    def verify_installation(self) -> bool:
        """Verify that Claude CLI is installed and accessible.

        Returns:
            True if CLI is available, False otherwise.
        """
        try:
            result = subprocess.run(
                [self.cli_path, "--version"],
                capture_output=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
```

---

## Section 7: Orchestration

### src/agentic_builder/orchestration/workflows.py

```python
"""Predefined workflow definitions."""
from dataclasses import dataclass, field
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
            StageDefinition("implementation", [AgentType.DEV_PYTHON], parallel=True),  # Dynamic
            StageDefinition("quality", [AgentType.CQR, AgentType.SR, AgentType.QE], parallel=True),
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
            StageDefinition("implementation", [AgentType.DEV_PYTHON], parallel=True),
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
            StageDefinition("verification", [AgentType.QE, AgentType.E2E], parallel=True),
        ],
    ),
}

def get_workflow(workflow_type: str) -> WorkflowDefinition | None:
    """Get a workflow definition by type."""
    return WORKFLOWS.get(workflow_type)

def list_workflows() -> list[WorkflowDefinition]:
    """List all available workflows."""
    return list(WORKFLOWS.values())
```

### src/agentic_builder/orchestration/engine.py

```python
"""Workflow execution engine."""
import asyncio
from typing import Callable, Awaitable
from agentic_builder.orchestration.workflows import get_workflow, WorkflowDefinition, StageDefinition
from agentic_builder.orchestration.stage_executor import execute_stage
from agentic_builder.storage import workflows as workflow_storage
from agentic_builder.storage import tasks as task_storage
from agentic_builder.core.constants import WorkflowStatus, StageStatus, TaskStatus
from agentic_builder.core.exceptions import WorkflowNotFoundError

EventHandler = Callable[[str, dict], Awaitable[None]]

class WorkflowEngine:
    """Orchestrates workflow execution."""

    def __init__(self):
        self._event_handlers: dict[str, list[EventHandler]] = {}

    def on_event(self, event: str, handler: EventHandler) -> None:
        """Register an event handler."""
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)

    async def _emit(self, event: str, data: dict) -> None:
        """Emit an event to handlers."""
        handlers = self._event_handlers.get(event, [])
        for handler in handlers:
            await handler(event, data)

    async def create_and_execute(
        self,
        workflow_type: str,
        description: str,
    ) -> str:
        """Create and execute a workflow."""
        # Get workflow definition
        workflow_def = get_workflow(workflow_type)
        if not workflow_def:
            raise WorkflowNotFoundError(f"Unknown workflow type: {workflow_type}")

        # Create workflow run
        workflow_id = workflow_storage.create_workflow(workflow_type, description)

        # Create stages
        for i, stage_def in enumerate(workflow_def.stages):
            workflow_storage.create_stage(
                workflow_run_id=workflow_id,
                stage_name=stage_def.name,
                stage_order=i,
                parallel=stage_def.parallel,
            )

        # Create initial task for PM
        task_storage.create_task(
            task_id=f"{workflow_id}_task_001",
            workflow_run_id=workflow_id,
            title=f"Analyze requirements: {description}",
            agent_type=workflow_def.stages[0].agent_types[0].value,
            description=description,
            priority="high",
            created_by="user",
        )

        # Execute workflow
        await self.execute(workflow_id)
        return workflow_id

    async def execute(self, workflow_id: str) -> None:
        """Execute a workflow."""
        workflow = workflow_storage.get_workflow(workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(f"Workflow not found: {workflow_id}")

        workflow_storage.update_workflow_status(workflow_id, WorkflowStatus.RUNNING)
        await self._emit("workflow_started", {"workflow_id": workflow_id})

        try:
            stages = workflow_storage.get_workflow_stages(workflow_id)

            for stage in stages:
                # Update stage status
                workflow_storage.update_stage_status(stage["id"], StageStatus.RUNNING)
                await self._emit("stage_started", {
                    "workflow_id": workflow_id,
                    "stage_id": stage["id"],
                    "stage_name": stage["stage_name"],
                })

                # Execute stage
                success = await execute_stage(
                    workflow_id=workflow_id,
                    stage_id=stage["id"],
                    parallel=bool(stage["parallel"]),
                )

                if success:
                    workflow_storage.update_stage_status(stage["id"], StageStatus.COMPLETED)
                    await self._emit("stage_completed", {
                        "workflow_id": workflow_id,
                        "stage_id": stage["id"],
                    })
                else:
                    workflow_storage.update_stage_status(stage["id"], StageStatus.FAILED)
                    await self._emit("stage_failed", {
                        "workflow_id": workflow_id,
                        "stage_id": stage["id"],
                    })
                    # Stop on failure
                    workflow_storage.update_workflow_status(
                        workflow_id, WorkflowStatus.FAILED,
                        error_message=f"Stage {stage['stage_name']} failed"
                    )
                    await self._emit("workflow_failed", {"workflow_id": workflow_id})
                    return

            # All stages completed
            workflow_storage.update_workflow_status(workflow_id, WorkflowStatus.COMPLETED)
            await self._emit("workflow_completed", {"workflow_id": workflow_id})

        except Exception as e:
            workflow_storage.update_workflow_status(
                workflow_id, WorkflowStatus.FAILED, error_message=str(e)
            )
            await self._emit("workflow_failed", {
                "workflow_id": workflow_id,
                "error": str(e),
            })
            raise

    async def pause(self, workflow_id: str) -> None:
        """Pause a running workflow."""
        workflow_storage.update_workflow_status(workflow_id, WorkflowStatus.PAUSED)

    async def resume(self, workflow_id: str) -> None:
        """Resume a paused workflow."""
        workflow = workflow_storage.get_workflow(workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(f"Workflow not found: {workflow_id}")
        if workflow["status"] not in (WorkflowStatus.PAUSED.value, WorkflowStatus.FAILED.value):
            raise ValueError(f"Cannot resume workflow in status: {workflow['status']}")
        await self.execute(workflow_id)

    async def cancel(self, workflow_id: str) -> None:
        """Cancel a workflow."""
        workflow_storage.update_workflow_status(workflow_id, WorkflowStatus.CANCELLED)
```

### src/agentic_builder/orchestration/stage_executor.py

```python
"""Stage execution with parallel/sequential support."""
import asyncio
from agentic_builder.storage import tasks as task_storage
from agentic_builder.agents.executor import execute_agent
from agentic_builder.context.serializer import build_task_context
from agentic_builder.core.constants import AgentType, TaskStatus

async def execute_stage(
    workflow_id: str,
    stage_id: str,
    parallel: bool = False,
) -> bool:
    """Execute all tasks in a stage."""
    # Get runnable tasks for this stage
    tasks = task_storage.get_workflow_tasks(workflow_id, status=TaskStatus.PENDING.value)
    stage_tasks = [t for t in tasks if t.get("stage_id") == stage_id]

    if not stage_tasks:
        # No tasks, might need to create them from previous stage output
        return True

    if parallel:
        # Execute tasks in parallel
        results = await asyncio.gather(
            *[execute_task(t) for t in stage_tasks],
            return_exceptions=True,
        )
        return all(not isinstance(r, Exception) and r for r in results)
    else:
        # Execute tasks sequentially
        for task in stage_tasks:
            success = await execute_task(task)
            if not success:
                return False
        return True

async def execute_task(task: dict) -> bool:
    """Execute a single task."""
    task_id = task["id"]
    workflow_id = task["workflow_run_id"]
    agent_type = AgentType(task["agent_type"])

    # Build context
    dependencies = task_storage.get_task_dependencies(task_id)
    dep_outputs = []
    for dep_id in dependencies:
        output = task_storage.get_task_output(dep_id)
        if output:
            dep_task = task_storage.get_task(dep_id)
            dep_outputs.append({
                "task_id": dep_id,
                "agent_type": dep_task["agent_type"] if dep_task else "",
                "summary": output.get("summary", ""),
                "key_decisions": output.get("key_decisions", []),
            })

    context_xml = build_task_context(
        task_id=task_id,
        agent_type=agent_type.value,
        workflow_id=workflow_id,
        summary=task.get("title", ""),
        requirements=[],  # Filled from task description
        constraints=[],
        dependencies=dep_outputs,
        artifacts=[],
        acceptance_criteria=[],
    )

    # Save context
    task_storage.save_task_context(task_id, context_xml, len(context_xml) // 4)

    # Execute agent
    try:
        response = await execute_agent(
            task_id=task_id,
            agent_type=agent_type,
            workflow_run_id=workflow_id,
            context_xml=context_xml,
        )
        return response.success
    except Exception:
        return False
```

---

## Section 8: CLI

### src/agentic_builder/cli/main.py

```python
"""Main CLI application."""
import typer
from rich.console import Console

from agentic_builder.cli.commands import (
    init_cmd,
    start,
    status,
    resume,
    cancel,
    logs,
    agents,
    tasks,
    usage,
)

app = typer.Typer(
    name="agentic-builder",
    help="AI-powered software project builder using orchestrated agents",
    no_args_is_help=True,
)
console = Console()

# Register commands
app.add_typer(init_cmd.app, name="init")
app.add_typer(start.app, name="start")
app.add_typer(status.app, name="status")
app.add_typer(resume.app, name="resume")
app.add_typer(cancel.app, name="cancel")
app.add_typer(logs.app, name="logs")
app.add_typer(agents.app, name="agents")
app.add_typer(tasks.app, name="tasks")
app.add_typer(usage.app, name="usage")

@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Agentic Builder - Build software projects with AI agents."""
    pass

if __name__ == "__main__":
    app()
```

### src/agentic_builder/cli/commands/init_cmd.py

```python
"""Initialize command."""
import typer
from pathlib import Path
from rich.console import Console

from agentic_builder.core.config import get_project_dir
from agentic_builder.storage.database import Database
from agentic_builder.api.claude_cli import ClaudeCLI

app = typer.Typer()
console = Console()

@app.callback(invoke_without_command=True)
def init(
    project_type: str = typer.Option("", "--type", "-t", help="Project type hint"),
    name: str = typer.Option("", "--name", "-n", help="Project name"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing"),
    skip_cli_check: bool = typer.Option(False, "--skip-cli-check", help="Skip Claude CLI verification"),
):
    """Initialize agentic-builder in the current directory."""
    project_dir = get_project_dir()

    # Verify Claude CLI is installed
    if not skip_cli_check:
        cli = ClaudeCLI()
        if not cli.verify_installation():
            console.print("[red]Error:[/red] Claude Code CLI not found.")
            console.print("\nPlease install Claude Code CLI:")
            console.print("  npm install -g @anthropic-ai/claude-code")
            console.print("\nOr specify custom path via AGENTIC_CLAUDE_CLI_PATH environment variable.")
            console.print("\nUse --skip-cli-check to bypass this verification.")
            raise typer.Exit(1)
        console.print("[green]✓[/green] Claude Code CLI found")

    if project_dir.exists() and not force:
        console.print("[red]Error:[/red] .agentic/ already exists. Use --force to overwrite.")
        raise typer.Exit(1)

    # Create directory structure
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "logs").mkdir(exist_ok=True)

    # Initialize database
    db = Database()
    db.initialize()

    # Set project name
    project_name = name or Path.cwd().name
    from agentic_builder.storage.database import get_db
    get_db().execute_write(
        "UPDATE config SET value = ? WHERE key = 'project_name'",
        (project_name,)
    )

    console.print(f"[green]Initialized agentic-builder in {project_dir}[/green]")
    console.print(f"Project: {project_name}")
    console.print("\nNext steps:")
    console.print("  agentic-builder start \"Describe what you want to build\"")
```

### src/agentic_builder/cli/commands/start.py

```python
"""Start command."""
import asyncio
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from agentic_builder.core.config import get_project_dir
from agentic_builder.core.exceptions import NotInitializedError
from agentic_builder.orchestration.engine import WorkflowEngine

app = typer.Typer()
console = Console()

@app.callback(invoke_without_command=True)
def start(
    description: str = typer.Argument(..., help="Description of what to build"),
    workflow: str = typer.Option("full_project", "--workflow", "-w", help="Workflow type"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show plan without executing"),
):
    """Start a new project from a description."""
    if not get_project_dir().exists():
        console.print("[red]Error:[/red] Not initialized. Run 'agentic-builder init' first.")
        raise typer.Exit(1)

    if dry_run:
        console.print(f"[yellow]Dry run:[/yellow] Would start '{workflow}' workflow")
        console.print(f"Description: {description}")
        return

    console.print(f"[blue]Starting workflow:[/blue] {workflow}")
    console.print(f"Description: {description}\n")

    async def run():
        engine = WorkflowEngine()

        # Register progress handlers
        async def on_stage(event: str, data: dict):
            if event == "stage_started":
                console.print(f"  [cyan]Stage:[/cyan] {data.get('stage_name', 'unknown')}")
            elif event == "stage_completed":
                console.print(f"  [green]Stage completed[/green]")

        engine.on_event("stage_started", on_stage)
        engine.on_event("stage_completed", on_stage)

        workflow_id = await engine.create_and_execute(workflow, description)
        console.print(f"\n[green]Workflow completed:[/green] {workflow_id}")

    asyncio.run(run())
```

### src/agentic_builder/cli/commands/status.py

```python
"""Status command."""
import typer
from rich.console import Console
from rich.table import Table

from agentic_builder.core.config import get_project_dir
from agentic_builder.storage import workflows as workflow_storage

app = typer.Typer()
console = Console()

@app.callback(invoke_without_command=True)
def status(
    workflow_id: str = typer.Option("", "--workflow-id", "-w", help="Specific workflow ID"),
    show_tasks: bool = typer.Option(False, "--tasks", "-t", help="Show task details"),
):
    """Show workflow status."""
    if not get_project_dir().exists():
        console.print("[red]Error:[/red] Not initialized.")
        raise typer.Exit(1)

    if workflow_id:
        workflow = workflow_storage.get_workflow(workflow_id)
    else:
        workflow = workflow_storage.get_latest_workflow()

    if not workflow:
        console.print("[yellow]No workflows found.[/yellow]")
        return

    # Status colors
    status_colors = {
        "pending": "yellow",
        "running": "blue",
        "completed": "green",
        "failed": "red",
        "cancelled": "dim",
        "paused": "yellow",
    }
    color = status_colors.get(workflow["status"], "white")

    console.print(f"\n[bold]Workflow:[/bold] {workflow['id']}")
    console.print(f"[bold]Type:[/bold] {workflow['workflow_type']}")
    console.print(f"[bold]Status:[/bold] [{color}]{workflow['status']}[/{color}]")
    console.print(f"[bold]Description:[/bold] {workflow['description']}")
    console.print(f"[bold]Tokens:[/bold] {workflow['total_tokens_used']:,}")
    console.print(f"[bold]Cost:[/bold] ${workflow['estimated_cost_usd']:.4f}")

    if workflow.get("error_message"):
        console.print(f"[bold red]Error:[/bold red] {workflow['error_message']}")

    if show_tasks:
        from agentic_builder.storage import tasks as task_storage
        tasks = task_storage.get_workflow_tasks(workflow["id"])

        if tasks:
            console.print("\n[bold]Tasks:[/bold]")
            table = Table()
            table.add_column("ID", style="dim")
            table.add_column("Agent")
            table.add_column("Title")
            table.add_column("Status")

            for task in tasks:
                task_color = status_colors.get(task["status"], "white")
                table.add_row(
                    task["id"],
                    task["agent_type"],
                    task["title"][:50],
                    f"[{task_color}]{task['status']}[/{task_color}]",
                )
            console.print(table)
```

Create similar implementations for the remaining commands:
- `resume.py` - Resume paused/failed workflows
- `cancel.py` - Cancel running workflows
- `logs.py` - View workflow logs
- `agents.py` - List available agents
- `tasks.py` - List tasks
- `usage.py` - Show token usage

Each command should follow the same pattern: check initialization, get relevant data from storage, display with rich formatting.

---

## Section 9: Agent Prompts

Create the following prompt files in `prompts/agents/`. Each prompt must follow this template structure:

### prompts/agents/product-manager.md

```markdown
# Product Manager (PM) - System Prompt

## Identity & Role

You are the **Product Manager** agent in the Agentic Builder framework. You are responsible for understanding user requirements, breaking them down into actionable tasks, and ensuring the project stays focused on delivering value.

### Position in Workflow

```
USER REQUEST
    |
    v
+------------------+
| PRODUCT MANAGER  | <-- You are here
|   (PM)           |
+------------------+
    |
    +---> ARCHITECT (system design)
    +---> RESEARCHER (investigation)
    +---> GD/UIUX (design)
```

## Core Responsibilities

1. **Requirements Analysis** - Extract clear requirements from user descriptions
2. **Task Creation** - Create well-defined, actionable tasks for other agents
3. **Prioritization** - Apply RICE scoring to prioritize work
4. **Scope Management** - Keep the project focused, prevent scope creep
5. **Acceptance Criteria** - Define measurable success criteria for each task

---

## Task Protocol

### Reading Your Task

Your task is provided in XML format:

```xml
<task_input>
  <meta>
    <task_id>TASK-XXXX</task_id>
    <agent_type>PM</agent_type>
    <workflow_id>wf_xxx</workflow_id>
  </meta>
  <summary>User's request or description</summary>
  <requirements>...</requirements>
  <constraints>...</constraints>
</task_input>
```

### Writing Your Output

```xml
<task_output>
  <success>true</success>
  <summary>Brief summary of requirements analysis</summary>

  <key_decisions>
    <decision>Decision 1 with rationale</decision>
    <decision>Decision 2 with rationale</decision>
  </key_decisions>

  <artifacts>
    <artifact type="requirements" name="requirements-doc">
      <description>Detailed requirements breakdown</description>
      <content>
        ## Project Requirements
        ...
      </content>
    </artifact>
  </artifacts>

  <next_tasks>
    <task agent="ARCH" priority="high">
      <title>Design system architecture</title>
      <description>Based on requirements, design the system architecture</description>
      <acceptance_criteria>
        <criterion>Architecture diagram created</criterion>
        <criterion>Technology stack selected with rationale</criterion>
        <criterion>API contracts defined</criterion>
      </acceptance_criteria>
    </task>
    <task agent="RESEARCH" priority="medium">
      <title>Research best practices for [topic]</title>
      <description>Investigate current best practices</description>
      <acceptance_criteria>
        <criterion>Summary of findings</criterion>
        <criterion>Recommendations</criterion>
      </acceptance_criteria>
    </task>
  </next_tasks>

  <warnings>
    <warning>Any risks or concerns</warning>
  </warnings>
</task_output>
```

---

## Quality Gates

Before completing your task, verify:

- [ ] All requirements are clear and unambiguous
- [ ] Each task has measurable acceptance criteria
- [ ] No task is too large (should be completable by one agent)
- [ ] Dependencies between tasks are clear
- [ ] Scope is realistic for the described project

## Anti-Patterns

- **Vague requirements**: "Make it good" - always be specific
- **Huge tasks**: "Build the entire backend" - break into smaller pieces
- **Missing criteria**: Tasks without acceptance criteria cannot be verified
- **Scope creep**: Adding features not in the original request
```

### Create similar prompts for all other agents:

- `architect.md` - System design, tech selection
- `researcher.md` - Investigation, analysis
- `graphical-designer.md` - Visual design
- `uiux-specialist.md` - UX design
- `code-quality-reviewer.md` - Code review
- `security-reviewer.md` - Security analysis
- `quality-engineer.md` - Test planning
- `e2e-tester.md` - E2E testing
- `task-quality-reviewer.md` - Task validation (critical - gates all tasks)
- `team-lead.md` - Template for TL variants
- `developer.md` - Template for DEV variants
- `devops-engineer.md` - Infrastructure

Each prompt should follow the same structure but with role-specific:
- Responsibilities
- Position in workflow diagram
- Input expectations
- Output format
- Quality gates
- Anti-patterns

---

## Section 10: Verification

After implementation, verify the following:

### Prerequisites Check

**Claude Code CLI Installation:**
```bash
# Verify Claude Code CLI is installed
claude --version
```
Expected: Shows version number (e.g., `claude-code/1.x.x`)

If not installed:
```bash
npm install -g @anthropic-ai/claude-code
```

### Installation Test
```bash
cd agentic-builder
pip install -e .
```
Expected: Installs without errors

### CLI Help Test
```bash
agentic-builder --help
```
Expected: Shows all commands with descriptions

### Init Test
```bash
mkdir /tmp/test-project
cd /tmp/test-project
agentic-builder init --name test-project
ls -la .agentic/
```
Expected:
- Outputs "✓ Claude Code CLI found"
- Creates `.agentic/` with `agentic.db` and `logs/`

### Database Test
```bash
sqlite3 .agentic/agentic.db ".tables"
```
Expected: Shows all tables (workflow_runs, tasks, etc.)

### Agents List Test
```bash
agentic-builder agents
```
Expected: Lists all 10+ agents with descriptions

### Dry Run Test
```bash
agentic-builder start "Build a simple CLI todo app" --dry-run
```
Expected: Shows workflow plan without executing

---

## Output Requirements

When you complete this implementation:

1. **All files created** in the specified directory structure
2. **All code compiles** without syntax errors
3. **Tests pass** (at minimum: imports work, CLI responds)
4. **Documentation** in README.md explaining usage

The implementation should be production-quality:
- Type hints throughout
- Docstrings on public functions
- Error handling for common cases
- Logging for debugging

---

## Implementation Order

1. Create directory structure and pyproject.toml
2. Implement core module (constants, config, exceptions)
3. Implement storage layer (schema, database, tasks, workflows)
4. Implement context module (serializer, windowing, budget)
5. Implement agents module (registry, prompt_loader, response_parser, executor)
6. Implement API client
7. Implement orchestration (workflows, engine, stage_executor)
8. Implement CLI (main, all commands)
9. Create all agent prompts
10. Test and verify

Begin implementation now.
