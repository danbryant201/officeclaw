"""
Tests for the Outclaw tasks module.
"""

from unittest.mock import MagicMock, patch


class TestTasksClient:
    """Test TasksClient operations."""

    @patch("outclaw.tasks.GraphClient")
    def test_list_task_lists(self, mock_client_class, sample_task_list):
        """Test listing task lists."""
        from outclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.get_all.return_value = [sample_task_list]
        mock_client_class.return_value = mock_client

        client = TasksClient()
        lists = client.list_task_lists()

        assert len(lists) == 1
        assert lists[0]["displayName"] == sample_task_list["displayName"]
        mock_client.get_all.assert_called_with("/me/todo/lists")

    @patch("outclaw.tasks.GraphClient")
    def test_list_tasks(self, mock_client_class, sample_tasks):
        """Test listing tasks in a list."""
        from outclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.get_all.return_value = sample_tasks
        mock_client_class.return_value = mock_client

        client = TasksClient()
        tasks = client.list_tasks("list-123")

        assert len(tasks) == 3
        mock_client.get_all.assert_called_once()
        call_args = mock_client.get_all.call_args
        assert "/me/todo/lists/list-123/tasks" in call_args[0][0]

    @patch("outclaw.tasks.GraphClient")
    def test_list_tasks_active_only(self, mock_client_class, sample_tasks):
        """Test listing only active tasks."""
        from outclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.get_all.return_value = [sample_tasks[0]]
        mock_client_class.return_value = mock_client

        client = TasksClient()
        client.list_tasks("list-123", status="active")

        call_args = mock_client.get_all.call_args
        params = call_args[1]["params"]
        assert "$filter" in params
        assert "status ne 'completed'" in params["$filter"]

    @patch("outclaw.tasks.GraphClient")
    def test_list_tasks_completed_only(self, mock_client_class, sample_tasks):
        """Test listing only completed tasks."""
        from outclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.get_all.return_value = [sample_tasks[1]]
        mock_client_class.return_value = mock_client

        client = TasksClient()
        client.list_tasks("list-123", status="completed")

        call_args = mock_client.get_all.call_args
        params = call_args[1]["params"]
        assert "$filter" in params
        assert "status eq 'completed'" in params["$filter"]

    @patch("outclaw.tasks.GraphClient")
    def test_get_task(self, mock_client_class, sample_task):
        """Test getting a specific task."""
        from outclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.get.return_value = sample_task
        mock_client_class.return_value = mock_client

        client = TasksClient()
        task = client.get_task("list-123", "task-123")

        assert task["title"] == sample_task["title"]
        mock_client.get.assert_called_with("/me/todo/lists/list-123/tasks/task-123")

    @patch("outclaw.tasks.GraphClient")
    def test_create_task(self, mock_client_class, sample_task):
        """Test creating a task."""
        from outclaw.tasks import TasksClient

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

    @patch("outclaw.tasks.GraphClient")
    def test_create_task_with_due_date(self, mock_client_class, sample_task):
        """Test creating task with due date."""
        from outclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.post.return_value = sample_task
        mock_client_class.return_value = mock_client

        client = TasksClient()
        client.create_task("list-123", "Complete report", due_date="2026-02-20")

        call_args = mock_client.post.call_args
        task_data = call_args[0][1]
        assert "dueDateTime" in task_data
        assert "2026-02-20" in task_data["dueDateTime"]["dateTime"]

    @patch("outclaw.tasks.GraphClient")
    def test_create_task_with_body(self, mock_client_class, sample_task):
        """Test creating task with description."""
        from outclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.post.return_value = sample_task
        mock_client_class.return_value = mock_client

        client = TasksClient()
        client.create_task("list-123", "Task", body="Task description")

        call_args = mock_client.post.call_args
        task_data = call_args[0][1]
        assert "body" in task_data
        assert task_data["body"]["content"] == "Task description"

    @patch("outclaw.tasks.GraphClient")
    def test_complete_task(self, mock_client_class, sample_task):
        """Test completing a task."""
        from outclaw.tasks import TasksClient

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

    @patch("outclaw.tasks.GraphClient")
    def test_complete_task_with_timestamp(self, mock_client_class, sample_task):
        """Test completing task with specific timestamp."""
        from outclaw.tasks import TasksClient

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

    @patch("outclaw.tasks.GraphClient")
    def test_reopen_task(self, mock_client_class, sample_task):
        """Test reopening a completed task."""
        from outclaw.tasks import TasksClient

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

    @patch("outclaw.tasks.GraphClient")
    def test_delete_task(self, mock_client_class):
        """Test deleting a task."""
        from outclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.delete.return_value = None
        mock_client_class.return_value = mock_client

        client = TasksClient()
        client.delete_task("list-123", "task-123")

        mock_client.delete.assert_called_with("/me/todo/lists/list-123/tasks/task-123")

    @patch("outclaw.tasks.GraphClient")
    def test_create_task_list(self, mock_client_class, sample_task_list):
        """Test creating a task list."""
        from outclaw.tasks import TasksClient

        mock_client = MagicMock()
        mock_client.post.return_value = sample_task_list
        mock_client_class.return_value = mock_client

        client = TasksClient()
        client.create_task_list("My New List")

        mock_client.post.assert_called_with(
            "/me/todo/lists",
            {"displayName": "My New List"},
        )

    @patch("outclaw.tasks.GraphClient")
    def test_update_task(self, mock_client_class, sample_task):
        """Test updating a task."""
        from outclaw.tasks import TasksClient

        mock_client = MagicMock()
        updated = {**sample_task, "title": "Updated title"}
        mock_client.patch.return_value = updated
        mock_client_class.return_value = mock_client

        client = TasksClient()
        result = client.update_task("list-123", "task-123", title="Updated title")

        assert result["title"] == "Updated title"
        call_args = mock_client.patch.call_args
        assert call_args[0][1]["title"] == "Updated title"
