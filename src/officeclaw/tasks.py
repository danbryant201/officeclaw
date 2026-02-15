"""
Task operations for Outclaw.

Provides Microsoft To Do task management through Microsoft Graph API.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from officeclaw.client import GraphClient


class TasksClient:
    """
    Client for Microsoft Graph Tasks (To Do) API.

    Example:
        client = TasksClient()
        lists = client.list_task_lists()
        tasks = client.list_tasks(list_id)
        client.create_task(list_id, "Buy groceries")
    """

    def __init__(self, graph_client: GraphClient | None = None) -> None:
        """Initialize tasks client."""
        self._client = graph_client or GraphClient()
        self._owns_client = graph_client is None

    def list_task_lists(self) -> list[dict[str, Any]]:
        """
        List all task lists.

        Returns:
            List of task list objects
        """
        return self._client.get_all("/me/todo/lists")

    def get_task_list(self, list_id: str) -> dict[str, Any]:
        """
        Get a specific task list.

        Args:
            list_id: Task list ID

        Returns:
            Task list object
        """
        return self._client.get(f"/me/todo/lists/{list_id}")

    def create_task_list(self, name: str) -> dict[str, Any]:
        """
        Create a new task list.

        Args:
            name: List name

        Returns:
            Created task list object
        """
        return self._client.post("/me/todo/lists", {"displayName": name})

    def delete_task_list(self, list_id: str) -> None:
        """Delete a task list."""
        self._client.delete(f"/me/todo/lists/{list_id}")

    def list_tasks(
        self,
        list_id: str,
        status: str | None = None,
        limit: int | None = None,
        select: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        List tasks in a task list.

        Args:
            list_id: Task list ID
            status: Filter by status ("completed", "notStarted", "inProgress")
            limit: Maximum tasks to return
            select: Fields to return

        Returns:
            List of task objects
        """
        params: dict[str, Any] = {}

        if select:
            params["$select"] = select

        if status:
            if status == "completed":
                params["$filter"] = "status eq 'completed'"
            elif status == "active":
                params["$filter"] = "status ne 'completed'"
            else:
                params["$filter"] = f"status eq '{status}'"

        return self._client.get_all(
            f"/me/todo/lists/{list_id}/tasks",
            params=params,
            limit=limit,
        )

    def get_task(self, list_id: str, task_id: str) -> dict[str, Any]:
        """
        Get a specific task.

        Args:
            list_id: Task list ID
            task_id: Task ID

        Returns:
            Task object with full details
        """
        return self._client.get(f"/me/todo/lists/{list_id}/tasks/{task_id}")

    def create_task(
        self,
        list_id: str,
        title: str,
        body: str | None = None,
        due_date: str | None = None,
        importance: str = "normal",
        reminder: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new task.

        Args:
            list_id: Task list ID
            title: Task title
            body: Task description
            due_date: Due date (YYYY-MM-DD)
            importance: "low", "normal", or "high"
            reminder: Reminder datetime (ISO format)

        Returns:
            Created task object
        """
        task: dict[str, Any] = {
            "title": title,
            "importance": importance,
        }

        if body:
            task["body"] = {
                "content": body,
                "contentType": "text",
            }

        if due_date:
            task["dueDateTime"] = {
                "dateTime": f"{due_date}T00:00:00.0000000",
                "timeZone": "UTC",
            }

        if reminder:
            task["reminderDateTime"] = {
                "dateTime": reminder,
                "timeZone": "UTC",
            }
            task["isReminderOn"] = True

        return self._client.post(f"/me/todo/lists/{list_id}/tasks", task)

    def update_task(
        self,
        list_id: str,
        task_id: str,
        title: str | None = None,
        body: str | None = None,
        due_date: str | None = None,
        importance: str | None = None,
    ) -> dict[str, Any]:
        """
        Update a task.

        Args:
            list_id: Task list ID
            task_id: Task ID
            title: New title
            body: New description
            due_date: New due date
            importance: New importance

        Returns:
            Updated task object
        """
        data: dict[str, Any] = {}

        if title is not None:
            data["title"] = title

        if body is not None:
            data["body"] = {
                "content": body,
                "contentType": "text",
            }

        if due_date is not None:
            if due_date:
                data["dueDateTime"] = {
                    "dateTime": f"{due_date}T00:00:00.0000000",
                    "timeZone": "UTC",
                }
            else:
                data["dueDateTime"] = None

        if importance is not None:
            data["importance"] = importance

        return self._client.patch(
            f"/me/todo/lists/{list_id}/tasks/{task_id}",
            data,
        )

    def complete_task(
        self,
        list_id: str,
        task_id: str,
        completed_at: str | None = None,
    ) -> dict[str, Any]:
        """
        Mark a task as completed.

        Args:
            list_id: Task list ID
            task_id: Task ID
            completed_at: Completion datetime (defaults to now)

        Returns:
            Updated task object
        """
        if completed_at is None:
            completed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.0000000Z")

        data = {
            "status": "completed",
            "completedDateTime": {
                "dateTime": completed_at,
                "timeZone": "UTC",
            },
        }

        return self._client.patch(
            f"/me/todo/lists/{list_id}/tasks/{task_id}",
            data,
        )

    def reopen_task(self, list_id: str, task_id: str) -> dict[str, Any]:
        """
        Reopen a completed task.

        Args:
            list_id: Task list ID
            task_id: Task ID

        Returns:
            Updated task object
        """
        data = {
            "status": "notStarted",
            "completedDateTime": None,
        }

        return self._client.patch(
            f"/me/todo/lists/{list_id}/tasks/{task_id}",
            data,
        )

    def delete_task(self, list_id: str, task_id: str) -> None:
        """Delete a task."""
        self._client.delete(f"/me/todo/lists/{list_id}/tasks/{task_id}")

    def close(self) -> None:
        """Close the client."""
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> TasksClient:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()
