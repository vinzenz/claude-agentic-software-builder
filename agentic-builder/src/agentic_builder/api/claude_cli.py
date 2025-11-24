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
from dataclasses import dataclass
from pathlib import Path
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
        system_prompt_file = None
        try:
            # Build command
            cmd = [
                self.cli_path,
                "--print",  # Headless mode
                "--output-format",
                "json",  # JSON output for parsing
                "--model",
                model,
                "--max-turns",
                str(max_turns),
            ]

            # Add system prompt if provided
            if system_prompt:
                # Write system prompt to temp file for --system-prompt-file
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".txt", delete=False
                ) as f:
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

            # Claude CLI outputs multiple JSON objects for streaming
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
            if system_prompt_file:
                try:
                    Path(system_prompt_file).unlink()
                except OSError:
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
