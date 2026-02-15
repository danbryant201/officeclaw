"""
Tests for the Outclaw CLI.

Tests command parsing, output formatting, and error handling.
"""

import json
from unittest.mock import MagicMock, patch

from click.testing import CliRunner


class TestCliHelp:
    """Test CLI help and version commands."""

    def test_help_shows_commands(self):
        """Test that --help shows available commands."""
        from outclaw.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "mail" in result.output.lower()
        assert "calendar" in result.output.lower()
        assert "tasks" in result.output.lower()
        assert "auth" in result.output.lower()

    def test_version_shows_version(self):
        """Test that --version shows version number."""
        from outclaw.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        assert "1." in result.output or "outclaw" in result.output.lower()

    def test_mail_help(self):
        """Test mail subcommand help."""
        from outclaw.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["mail", "--help"])

        assert result.exit_code == 0
        assert "list" in result.output
        assert "get" in result.output
        assert "send" in result.output

    def test_calendar_help(self):
        """Test calendar subcommand help."""
        from outclaw.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["calendar", "--help"])

        assert result.exit_code == 0
        assert "list" in result.output
        assert "create" in result.output

    def test_tasks_help(self):
        """Test tasks subcommand help."""
        from outclaw.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["tasks", "--help"])

        assert result.exit_code == 0
        assert "list-lists" in result.output
        assert "list" in result.output
        assert "create" in result.output
        assert "complete" in result.output

    def test_auth_help(self):
        """Test auth subcommand help."""
        from outclaw.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["auth", "--help"])

        assert result.exit_code == 0
        assert "login" in result.output
        assert "logout" in result.output
        assert "status" in result.output


class TestMailCommands:
    """Test mail-related CLI commands."""

    @patch("outclaw.cli.GraphClient")
    def test_mail_list_success(self, mock_client_class, sample_messages):
        """Test successful mail list command."""
        from outclaw.cli import main

        mock_client = MagicMock()
        mock_client.get_all.return_value = sample_messages
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(main, ["mail", "list", "--limit", "10"])

        assert result.exit_code == 0

    @patch("outclaw.cli.GraphClient")
    def test_mail_list_json_output(self, mock_client_class, sample_messages):
        """Test mail list outputs valid JSON."""
        from outclaw.cli import main

        mock_client = MagicMock()
        mock_client.get_all.return_value = sample_messages
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(main, ["--json", "mail", "list"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "status" in data
        assert data["status"] == "success"

    def test_mail_get_requires_message_id(self):
        """Test mail get requires message-id argument."""
        from outclaw.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["mail", "get"])

        assert result.exit_code != 0

    def test_mail_send_requires_options(self):
        """Test mail send requires all options."""
        from outclaw.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["mail", "send"])

        assert result.exit_code != 0


class TestCalendarCommands:
    """Test calendar-related CLI commands."""

    @patch("outclaw.cli.GraphClient")
    def test_calendar_list_with_dates(self, mock_client_class, sample_events):
        """Test calendar list with date range."""
        from outclaw.cli import main

        mock_client = MagicMock()
        mock_client.get_all.return_value = sample_events
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(
            main, ["calendar", "list", "--start", "2026-02-01", "--end", "2026-02-28"]
        )

        assert result.exit_code == 0

    def test_calendar_list_requires_dates(self):
        """Test calendar list requires start and end dates."""
        from outclaw.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["calendar", "list"])

        assert result.exit_code != 0

    def test_calendar_create_requires_options(self):
        """Test calendar create requires subject, start, end."""
        from outclaw.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["calendar", "create"])

        assert result.exit_code != 0


class TestTasksCommands:
    """Test tasks-related CLI commands."""

    @patch("outclaw.cli.GraphClient")
    def test_tasks_list_lists(self, mock_client_class, sample_task_list):
        """Test listing task lists."""
        from outclaw.cli import main

        mock_client = MagicMock()
        mock_client.get_all.return_value = [sample_task_list]
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(main, ["tasks", "list-lists"])

        assert result.exit_code == 0

    @patch("outclaw.cli.GraphClient")
    def test_tasks_complete(self, mock_client_class, sample_task):
        """Test completing a task."""
        from outclaw.cli import main

        mock_client = MagicMock()
        completed_task = {**sample_task, "status": "completed"}
        mock_client.patch.return_value = completed_task
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(
            main, ["tasks", "complete", "--list-id", "list-123", "--task-id", "task-123"]
        )

        assert result.exit_code == 0

    def test_tasks_list_requires_list_id(self):
        """Test tasks list requires list-id."""
        from outclaw.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["tasks", "list"])

        assert result.exit_code != 0


class TestAuthCommands:
    """Test authentication-related CLI commands."""

    @patch("outclaw.cli.TokenManager")
    def test_auth_status_not_authenticated(self, mock_token_manager):
        """Test auth status when not authenticated."""
        from outclaw.cli import main

        mock_manager = MagicMock()
        mock_manager.get_token_info.return_value = None
        mock_token_manager.return_value = mock_manager

        runner = CliRunner()
        result = runner.invoke(main, ["auth", "status"])

        assert "not" in result.output.lower() or "authenticated" in result.output.lower()

    @patch("outclaw.cli.TokenManager")
    def test_auth_logout(self, mock_token_manager):
        """Test auth logout clears tokens."""
        from outclaw.cli import main

        mock_manager = MagicMock()
        mock_token_manager.return_value = mock_manager

        runner = CliRunner()
        result = runner.invoke(main, ["auth", "logout"])

        assert result.exit_code == 0
        mock_manager.clear_tokens.assert_called_once()


class TestJsonOutput:
    """Test JSON output mode."""

    @patch("outclaw.cli.GraphClient")
    def test_json_flag_affects_output(self, mock_client_class, sample_messages):
        """Test that --json flag produces JSON output."""
        from outclaw.cli import main

        mock_client = MagicMock()
        mock_client.get_all.return_value = sample_messages
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(main, ["--json", "mail", "list"])

        # Should be valid JSON
        data = json.loads(result.output)
        assert "status" in data

    @patch("outclaw.cli.GraphClient")
    def test_json_output_structure(self, mock_client_class, sample_task_list):
        """Test JSON output has correct structure."""
        from outclaw.cli import main

        mock_client = MagicMock()
        mock_client.get_all.return_value = [sample_task_list]
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(main, ["--json", "tasks", "list-lists"])

        data = json.loads(result.output)
        assert data["status"] == "success"
        assert "data" in data
        assert isinstance(data["data"], list)
