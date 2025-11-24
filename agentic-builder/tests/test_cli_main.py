"""Tests for CLI main application."""

import re
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from agentic_builder.cli.main import app


def strip_ansi_codes(text: str) -> str:
    """Strip ANSI escape codes from text."""
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    return ansi_escape.sub('', text)


class TestCLIMain:
    """Test CLI main application."""

    @pytest.fixture
    def runner(self):
        """CLI test runner."""
        return CliRunner()

    def test_app_creation(self):
        """Test that the app is properly created."""
        assert app is not None
        assert app.info.name == "agentic-builder"
        assert "AI-powered software project builder" in app.info.help

    def test_app_no_args_help(self):
        """Test that app shows help when no args provided."""
        runner = CliRunner()
        result = runner.invoke(app, [])

        # Exit code can be 0 or 2 (usage error) - both show help
        assert result.exit_code in [0, 2], f"Unexpected exit code: {result.exit_code}"
        assert "AI-powered software project builder" in result.output
        assert "Usage:" in result.output

    def test_app_verbose_option(self):
        """Test verbose option handling."""
        runner = CliRunner()

        # Test with --help to see if verbose option is available
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        clean_output = strip_ansi_codes(result.output)
        assert "--verbose" in clean_output
        assert "--json" in clean_output

    def test_app_json_option(self):
        """Test JSON output option handling."""
        runner = CliRunner()

        # Test with --help to see if json option is available
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        clean_output = strip_ansi_codes(result.output)
        assert "--json" in clean_output

    def test_app_callback_execution(self):
        """Test that the main callback is executed."""
        runner = CliRunner()

        # The callback doesn't do anything visible, but we can test it doesn't crash
        with patch('agentic_builder.cli.main.console') as mock_console:
            result = runner.invoke(app, ["--verbose", "--help"])
            assert result.exit_code == 0
            # Callback should not print anything for help command
            mock_console.print.assert_not_called()


class TestCLICommands:
    """Test CLI command registration."""

    def test_commands_registered(self):
        """Test that all expected commands are registered."""
        runner = CliRunner()

        # Check main help shows available commands
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

        # Should show registered subcommands
        output = result.output
        assert "init" in output
        assert "start" in output
        assert "status" in output
        assert "resume" in output
        assert "cancel" in output
        assert "logs" in output
        assert "agents" in output
        assert "tasks" in output
        assert "usage" in output

    def test_init_command_available(self):
        """Test that init command is available."""
        runner = CliRunner()

        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        # Should show init-specific help
        assert "init" in result.output.lower()

    def test_start_command_available(self):
        """Test that start command is available."""
        runner = CliRunner()

        result = runner.invoke(app, ["start", "--help"])
        assert result.exit_code == 0
        # Should show start-specific help
        assert "start" in result.output.lower()

    def test_status_command_available(self):
        """Test that status command is available."""
        runner = CliRunner()

        result = runner.invoke(app, ["status", "--help"])
        assert result.exit_code == 0
        # Should show status-specific help
        assert "status" in result.output.lower()


class TestCLIIntegration:
    """Test CLI integration scenarios."""

    def test_command_execution_without_project(self):
        """Test that commands fail gracefully when no project is initialized."""
        runner = CliRunner()

        # Mock to simulate no project directory
        with patch('agentic_builder.cli.commands.start.get_project_dir') as mock_get_project_dir:
            from unittest.mock import MagicMock
            mock_project_dir = MagicMock()
            mock_project_dir.exists.return_value = False
            mock_get_project_dir.return_value = mock_project_dir

            result = runner.invoke(app, ["start", "test description"])
            assert result.exit_code == 1
            assert "Not initialized" in result.output

    def test_start_command_requires_description(self):
        """Test that start command requires a description."""
        runner = CliRunner()

        result = runner.invoke(app, ["start"])
        assert result.exit_code == 1
        assert "Description is required" in result.output

    def test_start_dry_run_mode(self):
        """Test start command in dry-run mode."""
        runner = CliRunner()

        with patch('agentic_builder.cli.commands.start.console') as mock_console, \
             patch('agentic_builder.cli.commands.start.get_project_dir') as mock_get_project_dir:

            # Mock project directory exists
            from unittest.mock import MagicMock
            mock_project_dir = MagicMock()
            mock_project_dir.exists.return_value = True
            mock_get_project_dir.return_value = mock_project_dir

            result = runner.invoke(app, ["start", "--dry-run", "test project"])
            assert result.exit_code == 0
            # Should print dry run information
            mock_console.print.assert_called()

    def test_start_list_workflows(self):
        """Test start command workflow listing."""
        runner = CliRunner()

        with patch('agentic_builder.cli.commands.start.console') as mock_console:
            result = runner.invoke(app, ["start", "--list"])
            assert result.exit_code == 0
            # Should print workflow list
            mock_console.print.assert_called()