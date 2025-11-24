# Agentic Builder

AI-powered software project builder using orchestrated agents.

## Overview

Agentic Builder is a CLI tool that orchestrates multiple AI agents to build software projects from natural language descriptions. It uses Claude Code CLI in headless mode for agent execution and stores all state in SQLite for persistence.

## Installation

### Prerequisites

1. **Python 3.11+**
2. **Claude Code CLI** - Install via npm:
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

### Install Agentic Builder

```bash
cd agentic-builder
pip install -e .
```

## Quick Start

```bash
# Initialize in your project directory
agentic-builder init

# Start a new project
agentic-builder start "Build a CLI todo app with SQLite storage"

# Check status
agentic-builder status

# View available agents
agentic-builder agents

# View token usage
agentic-builder usage
```

## Commands

| Command | Description |
|---------|-------------|
| `init` | Initialize agentic-builder in current directory |
| `start` | Start a new project from description |
| `status` | Show workflow status |
| `resume` | Resume a paused/failed workflow |
| `cancel` | Cancel a running workflow |
| `logs` | View workflow logs |
| `agents` | List available agents |
| `tasks` | List tasks in a workflow |
| `usage` | Show token usage statistics |

## Workflows

### Full Project
Complete project from idea to implementation:
1. Requirements (PM)
2. Research
3. Architecture
4. Design (parallel: GD, UIUX)
5. Task Review
6. Implementation (parallel developers)
7. Quality Review (parallel: CQR, SR, QE)
8. E2E Testing

### Add Feature
Add a feature to existing project:
1. Requirements (PM)
2. Architecture
3. Task Review
4. Implementation
5. Quality Review

### Fix Bug
Diagnose and fix a bug:
1. Analysis
2. Solution Design
3. Implementation
4. Verification

## Agent Types

| Agent | Model | Description |
|-------|-------|-------------|
| PM | Sonnet | Product Manager - requirements, task creation |
| ARCH | Opus | Architect - system design, tech selection |
| RESEARCH | Sonnet | Researcher - investigation, analysis |
| GD | Sonnet | Graphical Designer - visual design |
| UIUX | Sonnet | UI/UX Specialist - user flows, wireframes |
| CQR | Sonnet | Code Quality Reviewer - code review |
| SR | Opus | Security Reviewer - security analysis |
| QE | Sonnet | Quality Engineer - test planning |
| E2E | Sonnet | E2E Tester - end-to-end testing |
| TQR | Haiku | Task Quality Reviewer - task validation |
| DOE | Sonnet | DevOps Engineer - CI/CD, infrastructure |

## Configuration

Set environment variables or create `.env` file:

```bash
AGENTIC_DEFAULT_MODEL=sonnet
AGENTIC_MAX_CONCURRENT_AGENTS=3
AGENTIC_TOKEN_BUDGET=500000
AGENTIC_LOG_LEVEL=INFO
AGENTIC_CLAUDE_CLI_PATH=claude  # Custom path to Claude CLI
```

## Architecture

```
.agentic/
├── agentic.db      # SQLite database with all state
└── logs/           # Execution logs

src/agentic_builder/
├── cli/            # CLI commands (typer)
├── core/           # Constants, config, exceptions
├── storage/        # SQLite operations
├── agents/         # Agent registry, execution
├── orchestration/  # Workflow engine
├── context/        # XML serialization, windowing
└── api/            # Claude CLI wrapper
```

## License

MIT
