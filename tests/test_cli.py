"""
Tests for the Outclaw CLI.

Tests command parsing, output formatting, and error handling.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner


class TestCliHelp:
    """Test CLI help and version commands."""

    def test_help_shows_commands(self):
        """Test that --help shows available commands."""
        # Import here to ensure clean state
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
        # Version should be in output
        assert "outclaw" in result.output.lower() or "1." in result.output


class TestMailCommands:
    """Test mail-related CLI commands."""

    @patch("outclaw.cli.MailClient")
    def test_mail_list_success(self, mock_client_class, sample_messages):
        """Test successful mail list command."""
        from outclaw.cli import main
        
        # Set up mock
        mock_client = MagicMock()
        mock_client.list_messages.return_value = sample_messages
        mock_client_class.return_value = mock_client
        
        runner = CliRunner()
        result = runner.invoke(main, ["mail", "list", "--limit", "10"])
        
        assert result.exit_code == 0
        mock_client.list_messages.assert_called_once()

    @patch("outclaw.cli.MailClient")
    def test_mail_list_json_output(self, mock_client_class, sample_messages):
        """Test mail list outputs valid JSON."""
        from outclaw.cli import main
        
        mock_client = MagicMock()
        mock_client.list_messages.return_value = sample_messages
        mock_client_class.return_value = mock_client
        
        runner = CliRunner()
        result = runner.invoke(main, ["mail", "list", "--output", "json"])
        
        assert result.exit_code == 0
        # Output should be valid JSON
        data = json.loads(result.output)
        assert "status" in data or isinstance(data, list)

    @patch("outclaw.cli.MailClient")
    def test_mail_get_requires_message_id(self, mock_client_class):
        """Test mail get requires message-id argument."""
        from outclaw.cli import main
        
        runner = CliRunner()
        result = runner.invoke(main, ["mail", "get"])
        
        # Should fail without message-id
        assert result.exit_code != 0
        assert "message-id" in result.output.lower() or "missing" in result.output.lower()


class TestCalendarCommands:
    """Test calendar-related CLI commands."""

    @patch("outclaw.cli.CalendarClient")
    def test_calendar_list_with_dates(self, mock_client_class, sample_events):
        """Test calendar list with date range."""
        from outclaw.cli import main
        
        mock_client = MagicMock()
        mock_client.list_events.return_value = sample_events
        mock_client_class.return_value = mock_client
        
        runner = CliRunner()
        result = runner.invoke(main, [
            "calendar", "list",
            "--start", "2026-02-01",
            "--end", "2026-02-28"
        ])
        
        assert result.exit_code == 0
        mock_client.list_events.assert_called_once()


class TestTasksCommands:
    """Test tasks-related CLI commands."""

    @patch("outclaw.cli.TasksClient")
    def test_tasks_list_lists(self, mock_client_class, sample_task_list):
        """Test listing task lists."""
        from outclaw.cli import main
        
        mock_client = MagicMock()
        mock_client.list_task_lists.return_value = [sample_task_list]
        mock_client_class.return_value = mock_client
        
        runner = CliRunner()
        result = runner.invoke(main, ["tasks", "list-lists"])
        
        assert result.exit_code == 0
        mock_client.list_task_lists.assert_called_once()

    @patch("outclaw.cli.TasksClient")
    def test_tasks_complete(self, mock_client_class, sample_task):
        """Test completing a task."""
        from outclaw.cli import main
        
        mock_client = MagicMock()
        completed_task = {**sample_task, "status": "completed"}
        mock_client.complete_task.return_value = completed_task
        mock_client_class.return_value = mock_client
        
        runner = CliRunner()
        result = runner.invoke(main, [
            "tasks", "complete",
            "--list-id", "list-123",
            "--task-id", "task-123"
        ])
        
        assert result.exit_code == 0


class TestAuthCommands:
    """Test authentication-related CLI commands."""

    @patch("outclaw.cli.TokenManager")
    def test_auth_status_not_authenticated(self, mock_token_manager):
        """Test auth status when not authenticated."""
        from outclaw.cli import main
        
        mock_manager = MagicMock()
        mock_manager.get_token.return_value = None
        mock_token_manager.return_value = mock_manager
        
        runner = CliRunner()
        result = runner.invoke(main, ["auth", "status"])
        
        # Should indicate not authenticated
        assert "not" in result.output.lower() or "no" in result.output.lower()

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


class TestErrorHandling:
    """Test CLI error handling."""

    @patch("outclaw.cli.MailClient")
    def test_authentication_error_message(self, mock_client_class):
        """Test authentication error shows helpful message."""
        from outclaw.cli import main
        from outclaw.exceptions import AuthenticationError
        
        mock_client = MagicMock()
        mock_client.list_messages.side_effect = AuthenticationError("Token expired")
        mock_client_class.return_value = mock_client
        
        runner = CliRunner()
        result = runner.invoke(main, ["mail", "list"])
        
        # Should show authentication error
        assert result.exit_code != 0
        assert "auth" in result.output.lower() or "token" in result.output.lower()

    @patch("outclaw.cli.MailClient")
    def test_api_error_shows_details(self, mock_client_class):
        """Test API error shows error details."""
        from outclaw.cli import main
        from outclaw.exceptions import GraphAPIError
        
        mock_client = MagicMock()
        mock_client.list_messages.side_effect = GraphAPIError(
            "ResourceNotFound", "Message not found"
        )
        mock_client_class.return_value = mock_client
        
        runner = CliRunner()
        result = runner.invoke(main, ["mail", "list"])
        
        assert result.exit_code != 0
        # Error details should be in output
        assert "error" in result.output.lower()
