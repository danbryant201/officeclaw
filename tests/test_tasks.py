"""
Tests for the Outclaw tasks module.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


class TestParseRecurrence:
    """Tests for _parse_recurrence helper."""

    def test_daily(self):
        from officeclaw.tasks import _parse_recurrence

        result = _parse_recurrence("daily", "2026-04-18")
        assert result["pattern"]["type"] == "daily"
        assert result["pattern"]["interval"] == 1
        assert result["range"]["startDate"] == "2026-04-18"

    def test_daily_with_interval(self):
        from officeclaw.tasks import _parse_recurrence

        result = _parse_recurrence("daily:3", "2026-04-18")
        assert result["pattern"]["interval"] == 3

    def test_weekly(self):
        from officeclaw.tasks import _parse_recurrence

        result = _parse_recurrence("weekly", "2026-04-18")
        assert result["pattern"]["type"] == "weekly"
        assert "daysOfWeek" not in result["pattern"]

    def test_weekly_with_days(self):
        from officeclaw.tasks import _parse_recurrence

        result = _parse_recurrence("weekly:MON,WED", "2026-04-18")
        assert result["pattern"]["daysOfWeek"] == ["monday", "wednesday"]
        assert result["pattern"]["firstDayOfWeek"] == "sunday"

    def test_weekdays(self):
        from officeclaw.tasks import _parse_recurrence

        result = _parse_recurrence("weekdays", "2026-04-18")
        assert result["pattern"]["daysOfWeek"] == [
            "monday", "tuesday", "wednesday", "thursday", "friday"
        ]

    def test_monthly(self):
        from officeclaw.tasks import _parse_recurrence

        result = _parse_recurrence("monthly", "2026-04-18")
        assert result["pattern"]["type"] == "absoluteMonthly"
        assert result["pattern"]["dayOfMonth"] == 18

    def test_monthly_with_day(self):
        from officeclaw.tasks import _parse_recurrence

        result = _parse_recurrence("monthly:15", "2026-04-18")
        assert result["pattern"]["dayOfMonth"] == 15

    def test_yearly(self):
        from officeclaw.tasks import _parse_recurrence

        result = _parse_recurrence("yearly", "2026-04-18")
        assert result["pattern"]["type"] == "absoluteYearly"

    def test_invalid_raises(self):
        from officeclaw.tasks import _parse_recurrence

        with pytest.raises(ValueError, match="Unrecognised repeat pattern"):
            _parse_recurrence("fortnightly", "2026-04-18")

    def test_range_is_no_end(self):
        from officeclaw.tasks import _parse_recurrence

        result = _parse_recurrence("daily", "2026-04-18")
        assert result["range"]["type"] == "noEnd"


class TestTasksClient:
    """Test TasksClient operations."""

    @patch("officeclaw.tasks.GraphClient")
    def test_list_task_lists(self, mock_client_class, sample_task_list):
        """Test listing task lists."""
        from officeclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.get_all.return_value = [sample_task_list]
        mock_client_class.return_value = mock_client

        client = TasksClient()
        lists = client.list_task_lists()

        assert len(lists) == 1
        assert lists[0]["displayName"] == sample_task_list["displayName"]
        mock_client.get_all.assert_called_with("/me/todo/lists")

    @patch("officeclaw.tasks.GraphClient")
    def test_list_tasks(self, mock_client_class, sample_tasks):
        """Test listing tasks in a list."""
        from officeclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.get_all.return_value = sample_tasks
        mock_client_class.return_value = mock_client

        client = TasksClient()
        tasks = client.list_tasks("list-123")

        assert len(tasks) == 3
        mock_client.get_all.assert_called_once()
        call_args = mock_client.get_all.call_args
        assert "/me/todo/lists/list-123/tasks" in call_args[0][0]

    @patch("officeclaw.tasks.GraphClient")
    def test_list_tasks_active_only(self, mock_client_class, sample_tasks):
        """Test listing only active tasks."""
        from officeclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.get_all.return_value = [sample_tasks[0]]
        mock_client_class.return_value = mock_client

        client = TasksClient()
        client.list_tasks("list-123", status="active")

        call_args = mock_client.get_all.call_args
        params = call_args[1]["params"]
        assert "$filter" in params
        assert "status ne 'completed'" in params["$filter"]

    @patch("officeclaw.tasks.GraphClient")
    def test_list_tasks_completed_only(self, mock_client_class, sample_tasks):
        """Test listing only completed tasks."""
        from officeclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.get_all.return_value = [sample_tasks[1]]
        mock_client_class.return_value = mock_client

        client = TasksClient()
        client.list_tasks("list-123", status="completed")

        call_args = mock_client.get_all.call_args
        params = call_args[1]["params"]
        assert "$filter" in params
        assert "status eq 'completed'" in params["$filter"]

    @patch("officeclaw.tasks.GraphClient")
    def test_get_task(self, mock_client_class, sample_task):
        """Test getting a specific task."""
        from officeclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.get.return_value = sample_task
        mock_client_class.return_value = mock_client

        client = TasksClient()
        task = client.get_task("list-123", "task-123")

        assert task["title"] == sample_task["title"]
        mock_client.get.assert_called_with("/me/todo/lists/list-123/tasks/task-123")

    @patch("officeclaw.tasks.GraphClient")
    def test_create_task(self, mock_client_class, sample_task):
        """Test creating a task."""
        from officeclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.post.return_value = sample_task
        mock_client_class.return_value = mock_client

        client = TasksClient()
        task = client.create_task("list-123", "Complete report")

        assert task["title"] == sample_task["title"]
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/me/todo/lists/list-123/tasks"
        assert call_args[0][1]["title"] == "Complete report"

    @patch("officeclaw.tasks.GraphClient")
    def test_create_task_with_due_date(self, mock_client_class, sample_task):
        """Test creating task with due date."""
        from officeclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.post.return_value = sample_task
        mock_client_class.return_value = mock_client

        client = TasksClient()
        client.create_task("list-123", "Complete report", due_date="2026-02-20")

        call_args = mock_client.post.call_args
        task_data = call_args[0][1]
        assert "dueDateTime" in task_data
        assert "2026-02-20" in task_data["dueDateTime"]["dateTime"]

    @patch("officeclaw.tasks.GraphClient")
    def test_create_task_with_body(self, mock_client_class, sample_task):
        """Test creating task with description."""
        from officeclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.post.return_value = sample_task
        mock_client_class.return_value = mock_client

        client = TasksClient()
        client.create_task("list-123", "Task", body="Task description")

        call_args = mock_client.post.call_args
        task_data = call_args[0][1]
        assert "body" in task_data
        assert task_data["body"]["content"] == "Task description"

    @patch("officeclaw.tasks.GraphClient")
    def test_complete_task(self, mock_client_class, sample_task):
        """Test completing a task."""
        from officeclaw.tasks import TasksClient

        mock_client = MagicMock()
        completed = {**sample_task, "status": "completed"}
        mock_client.patch.return_value = completed
        mock_client_class.return_value = mock_client

        client = TasksClient()
        result = client.complete_task("list-123", "task-123")

        assert result["status"] == "completed"
        call_args = mock_client.patch.call_args
        assert call_args[0][0] == "/me/todo/lists/list-123/tasks/task-123"
        assert call_args[0][1]["status"] == "completed"
        assert "completedDateTime" in call_args[0][1]

    @patch("officeclaw.tasks.GraphClient")
    def test_complete_task_with_timestamp(self, mock_client_class, sample_task):
        """Test completing task with specific timestamp."""
        from officeclaw.tasks import TasksClient

        mock_client = MagicMock()
        completed = {**sample_task, "status": "completed"}
        mock_client.patch.return_value = completed
        mock_client_class.return_value = mock_client

        client = TasksClient()
        client.complete_task(
            "list-123",
            "task-123",
            completed_at="2026-02-12T15:30:00.0000000Z",
        )

        call_args = mock_client.patch.call_args
        assert call_args[0][1]["completedDateTime"]["dateTime"] == "2026-02-12T15:30:00.0000000Z"

    @patch("officeclaw.tasks.GraphClient")
    def test_reopen_task(self, mock_client_class, sample_task):
        """Test reopening a completed task."""
        from officeclaw.tasks import TasksClient

        mock_client = MagicMock()
        reopened = {**sample_task, "status": "notStarted"}
        mock_client.patch.return_value = reopened
        mock_client_class.return_value = mock_client

        client = TasksClient()
        result = client.reopen_task("list-123", "task-123")

        assert result["status"] == "notStarted"
        call_args = mock_client.patch.call_args
        assert call_args[0][1]["status"] == "notStarted"
        assert call_args[0][1]["completedDateTime"] is None

    @patch("officeclaw.tasks.GraphClient")
    def test_delete_task(self, mock_client_class):
        """Test deleting a task."""
        from officeclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.delete.return_value = None
        mock_client_class.return_value = mock_client

        client = TasksClient()
        client.delete_task("list-123", "task-123")

        mock_client.delete.assert_called_with("/me/todo/lists/list-123/tasks/task-123")

    @patch("officeclaw.tasks.GraphClient")
    def test_create_task_list(self, mock_client_class, sample_task_list):
        """Test creating a task list."""
        from officeclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.post.return_value = sample_task_list
        mock_client_class.return_value = mock_client

        client = TasksClient()
        client.create_task_list("My New List")

        mock_client.post.assert_called_with(
            "/me/todo/lists",
            {"displayName": "My New List"},
        )

    @patch("officeclaw.tasks.GraphClient")
    def test_update_task(self, mock_client_class, sample_task):
        """Test updating a task."""
        from officeclaw.tasks import TasksClient

        mock_client = MagicMock()
        updated = {**sample_task, "title": "Updated title"}
        mock_client.patch.return_value = updated
        mock_client_class.return_value = mock_client

        client = TasksClient()
        result = client.update_task("list-123", "task-123", title="Updated title")

        assert result["title"] == "Updated title"
        call_args = mock_client.patch.call_args
        assert call_args[0][1]["title"] == "Updated title"

    @patch("officeclaw.tasks.GraphClient")
    def test_create_task_add_to_my_day(self, mock_client_class, sample_task):
        from officeclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.post.return_value = sample_task
        mock_client_class.return_value = mock_client

        TasksClient().create_task("list-123", "Task", add_to_my_day=True, due_date="2026-04-20")

        task_data = mock_client.post.call_args[0][1]
        assert "startDateTime" in task_data
        assert "2026-04-20" in task_data["startDateTime"]["dateTime"]

    @patch("officeclaw.tasks.GraphClient")
    def test_create_task_add_to_my_day_defaults_to_today(self, mock_client_class, sample_task):
        from officeclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.post.return_value = sample_task
        mock_client_class.return_value = mock_client

        TasksClient().create_task("list-123", "Task", add_to_my_day=True)

        task_data = mock_client.post.call_args[0][1]
        assert "startDateTime" in task_data

    @patch("officeclaw.tasks.GraphClient")
    def test_create_task_with_recurrence(self, mock_client_class, sample_task):
        from officeclaw.tasks import TasksClient, _parse_recurrence

        mock_client = MagicMock()
        mock_client.post.return_value = sample_task
        mock_client_class.return_value = mock_client

        recurrence = _parse_recurrence("weekly:MON", "2026-04-18")
        TasksClient().create_task("list-123", "Task", recurrence=recurrence)

        task_data = mock_client.post.call_args[0][1]
        assert task_data["recurrence"]["pattern"]["type"] == "weekly"

    @patch("officeclaw.tasks.GraphClient")
    def test_create_task_with_assignee(self, mock_client_class, sample_task):
        from officeclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.post.return_value = sample_task
        mock_client_class.return_value = mock_client

        TasksClient().create_task("list-123", "Task", assignee="alice@example.com")

        task_data = mock_client.post.call_args[0][1]
        assert task_data["assignedTo"] == "alice@example.com"

    @patch("officeclaw.tasks.GraphClient")
    def test_update_task_set_reminder(self, mock_client_class, sample_task):
        from officeclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.patch.return_value = sample_task
        mock_client_class.return_value = mock_client

        TasksClient().update_task(
            "list-123", "task-123", reminder="2026-04-20T09:00:00"
        )

        data = mock_client.patch.call_args[0][1]
        assert data["isReminderOn"] is True
        assert data["reminderDateTime"]["dateTime"] == "2026-04-20T09:00:00"

    @patch("officeclaw.tasks.GraphClient")
    def test_update_task_clear_reminder(self, mock_client_class, sample_task):
        from officeclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.patch.return_value = sample_task
        mock_client_class.return_value = mock_client

        TasksClient().update_task("list-123", "task-123", reminder_off=True)

        data = mock_client.patch.call_args[0][1]
        assert data["isReminderOn"] is False
        assert data["reminderDateTime"] is None

    @patch("officeclaw.tasks.GraphClient")
    def test_update_task_reminder_off_wins_over_reminder(self, mock_client_class, sample_task):
        from officeclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.patch.return_value = sample_task
        mock_client_class.return_value = mock_client

        TasksClient().update_task(
            "list-123", "task-123",
            reminder="2026-04-20T09:00:00",
            reminder_off=True,
        )

        data = mock_client.patch.call_args[0][1]
        assert data["isReminderOn"] is False

    @patch("officeclaw.tasks.GraphClient")
    def test_update_task_add_to_my_day(self, mock_client_class, sample_task):
        from officeclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.patch.return_value = sample_task
        mock_client_class.return_value = mock_client

        TasksClient().update_task("list-123", "task-123", add_to_my_day=True)

        data = mock_client.patch.call_args[0][1]
        assert "startDateTime" in data

    @patch("officeclaw.tasks.GraphClient")
    def test_update_task_remove_from_my_day(self, mock_client_class, sample_task):
        from officeclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.patch.return_value = sample_task
        mock_client_class.return_value = mock_client

        TasksClient().update_task("list-123", "task-123", add_to_my_day=False)

        data = mock_client.patch.call_args[0][1]
        assert data["startDateTime"] is None

    @patch("officeclaw.tasks.GraphClient")
    def test_update_task_my_day_none_omitted(self, mock_client_class, sample_task):
        from officeclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.patch.return_value = sample_task
        mock_client_class.return_value = mock_client

        TasksClient().update_task("list-123", "task-123", title="x")

        data = mock_client.patch.call_args[0][1]
        assert "startDateTime" not in data

    @patch("officeclaw.tasks.GraphClient")
    def test_update_task_clear_recurrence(self, mock_client_class, sample_task):
        from officeclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.patch.return_value = sample_task
        mock_client_class.return_value = mock_client

        TasksClient().update_task("list-123", "task-123", recurrence_off=True)

        data = mock_client.patch.call_args[0][1]
        assert data["recurrence"] is None

    @patch("officeclaw.tasks.GraphClient")
    def test_get_task_list_members_not_shared(self, mock_client_class, sample_task_list):
        from officeclaw.tasks import TasksClient
        from officeclaw.exceptions import GraphAPIError

        mock_client = MagicMock()
        mock_client.get.return_value = {**sample_task_list, "isShared": False}
        mock_client_class.return_value = mock_client

        with pytest.raises(GraphAPIError) as exc_info:
            TasksClient().get_task_list_members("list-123")

        assert exc_info.value.code == "ListNotShared"

    @patch("officeclaw.tasks.GraphClient")
    def test_get_task_list_members_404_returns_empty(self, mock_client_class, sample_task_list):
        from officeclaw.tasks import TasksClient
        from officeclaw.exceptions import GraphAPIError

        mock_client = MagicMock()
        mock_client.get.return_value = {**sample_task_list, "isShared": True}
        mock_client.get_all.side_effect = GraphAPIError("NotFound", "Not found", 404)
        mock_client_class.return_value = mock_client

        assert TasksClient().get_task_list_members("list-123") == []

    @patch("officeclaw.tasks.GraphClient")
    def test_get_task_list_members_bad_request_returns_empty(self, mock_client_class, sample_task_list):
        from officeclaw.tasks import TasksClient
        from officeclaw.exceptions import GraphAPIError

        mock_client = MagicMock()
        mock_client.get.return_value = {**sample_task_list, "isShared": True}
        mock_client.get_all.side_effect = GraphAPIError(
            "BadRequest", "Resource not found for the segment 'members'", 400
        )
        mock_client_class.return_value = mock_client

        assert TasksClient().get_task_list_members("list-123") == []

    @patch("officeclaw.tasks.GraphClient")
    def test_list_checklist_items(self, mock_client_class, sample_checklist_item):
        from officeclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.get_all.return_value = [sample_checklist_item]
        mock_client_class.return_value = mock_client

        items = TasksClient().list_checklist_items("list-123", "task-123")

        assert len(items) == 1
        mock_client.get_all.assert_called_with(
            "/me/todo/lists/list-123/tasks/task-123/checklistItems"
        )

    @patch("officeclaw.tasks.GraphClient")
    def test_add_checklist_item(self, mock_client_class, sample_checklist_item):
        from officeclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.post.return_value = sample_checklist_item
        mock_client_class.return_value = mock_client

        result = TasksClient().add_checklist_item("list-123", "task-123", "Buy milk")

        assert result["displayName"] == "Buy milk"
        mock_client.post.assert_called_with(
            "/me/todo/lists/list-123/tasks/task-123/checklistItems",
            {"displayName": "Buy milk"},
        )

    @patch("officeclaw.tasks.GraphClient")
    def test_complete_checklist_item(self, mock_client_class, sample_checklist_item):
        from officeclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.patch.return_value = {**sample_checklist_item, "isChecked": True}
        mock_client_class.return_value = mock_client

        result = TasksClient().complete_checklist_item("list-123", "task-123", "item-123")

        assert result["isChecked"] is True
        mock_client.patch.assert_called_with(
            "/me/todo/lists/list-123/tasks/task-123/checklistItems/item-123",
            {"isChecked": True},
        )

    @patch("officeclaw.tasks.GraphClient")
    def test_delete_checklist_item(self, mock_client_class):
        from officeclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.delete.return_value = None
        mock_client_class.return_value = mock_client

        TasksClient().delete_checklist_item("list-123", "task-123", "item-123")

        mock_client.delete.assert_called_with(
            "/me/todo/lists/list-123/tasks/task-123/checklistItems/item-123"
        )
