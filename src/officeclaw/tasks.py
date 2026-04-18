"""
Task operations for Outclaw.

Provides Microsoft To Do task management through Microsoft Graph API.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from officeclaw.client import GraphClient
from officeclaw.exceptions import GraphAPIError

_DAY_MAP = {
    "MON": "monday",
    "TUE": "tuesday",
    "WED": "wednesday",
    "THU": "thursday",
    "FRI": "friday",
    "SAT": "saturday",
    "SUN": "sunday",
}


def _parse_recurrence(repeat_str: str, start_date: str) -> dict[str, Any]:
    """Parse a repeat shorthand string into a Graph API patternedRecurrence dict."""
    parts = repeat_str.split(":", 1)
    kind = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else None

    day_of_month = int(start_date.split("-")[2])
    range_ = {"type": "noEnd", "startDate": start_date}

    if kind == "daily":
        interval = int(arg) if arg else 1
        return {"pattern": {"type": "daily", "interval": interval}, "range": range_}

    if kind == "weekly":
        pattern: dict[str, Any] = {"type": "weekly", "interval": 1}
        if arg:
            days = [_DAY_MAP[d.strip().upper()] for d in arg.split(",")]
            pattern["daysOfWeek"] = days
            pattern["firstDayOfWeek"] = "sunday"
        return {"pattern": pattern, "range": range_}

    if kind == "weekdays":
        return {
            "pattern": {
                "type": "weekly",
                "interval": 1,
                "daysOfWeek": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                "firstDayOfWeek": "sunday",
            },
            "range": range_,
        }

    if kind == "monthly":
        dom = int(arg) if arg else day_of_month
        return {
            "pattern": {"type": "absoluteMonthly", "interval": 1, "dayOfMonth": dom},
            "range": range_,
        }

    if kind == "yearly":
        return {"pattern": {"type": "absoluteYearly", "interval": 1}, "range": range_}

    raise ValueError(
        f"Unrecognised repeat pattern: {repeat_str!r}. "
        "Expected: daily, daily:N, weekly, weekly:MON,WED, monthly, monthly:15, yearly, weekdays"
    )


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

    def get_task_list_members(self, list_id: str) -> list[dict[str, Any]]:
        """Return members of a shared list, or [] if endpoint is unsupported."""
        info = self._client.get(f"/me/todo/lists/{list_id}")
        if not info.get("isShared"):
            raise GraphAPIError(
                "ListNotShared",
                "Task list is not shared; assignment requires a shared list.",
                400,
            )
        try:
            return self._client.get_all(f"/me/todo/lists/{list_id}/members")
        except GraphAPIError as e:
            if e.status_code == 404:
                return []
            raise

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
        add_to_my_day: bool = False,
        recurrence: dict | None = None,
        assignee: str | None = None,
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
            add_to_my_day: Pin to My Day
            recurrence: patternedRecurrence dict (use _parse_recurrence)
            assignee: Email to assign to (shared lists only)

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

        if add_to_my_day:
            anchor = due_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
            task["startDateTime"] = {
                "dateTime": f"{anchor}T00:00:00.0000000",
                "timeZone": "UTC",
            }

        if recurrence is not None:
            task["recurrence"] = recurrence

        if assignee is not None:
            task["assignedTo"] = assignee

        return self._client.post(f"/me/todo/lists/{list_id}/tasks", task)

    def update_task(
        self,
        list_id: str,
        task_id: str,
        title: str | None = None,
        body: str | None = None,
        due_date: str | None = None,
        importance: str | None = None,
        reminder: str | None = None,
        reminder_off: bool = False,
        add_to_my_day: bool | None = None,
        recurrence: dict | None = None,
        recurrence_off: bool = False,
        assignee: str | None = None,
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
            reminder: Set reminder (ISO datetime)
            reminder_off: Clear reminder
            add_to_my_day: True=add, False=remove, None=no change
            recurrence: Set recurrence (patternedRecurrence dict)
            recurrence_off: Clear recurrence
            assignee: Assign to email (shared lists only)

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

        if reminder_off:
            data["reminderDateTime"] = None
            data["isReminderOn"] = False
        elif reminder is not None:
            data["reminderDateTime"] = {"dateTime": reminder, "timeZone": "UTC"}
            data["isReminderOn"] = True

        if add_to_my_day is True:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            data["startDateTime"] = {"dateTime": f"{today}T00:00:00.0000000", "timeZone": "UTC"}
        elif add_to_my_day is False:
            data["startDateTime"] = None

        if recurrence_off:
            data["recurrence"] = None
        elif recurrence is not None:
            data["recurrence"] = recurrence

        if assignee is not None:
            data["assignedTo"] = assignee

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

    def list_checklist_items(self, list_id: str, task_id: str) -> list[dict[str, Any]]:
        """List checklist items (steps) for a task."""
        return self._client.get_all(
            f"/me/todo/lists/{list_id}/tasks/{task_id}/checklistItems"
        )

    def add_checklist_item(
        self, list_id: str, task_id: str, display_name: str
    ) -> dict[str, Any]:
        """Add a checklist item (step) to a task."""
        return self._client.post(
            f"/me/todo/lists/{list_id}/tasks/{task_id}/checklistItems",
            {"displayName": display_name},
        )

    def complete_checklist_item(
        self, list_id: str, task_id: str, item_id: str
    ) -> dict[str, Any]:
        """Mark a checklist item as checked."""
        return self._client.patch(
            f"/me/todo/lists/{list_id}/tasks/{task_id}/checklistItems/{item_id}",
            {"isChecked": True},
        )

    def delete_checklist_item(self, list_id: str, task_id: str, item_id: str) -> None:
        """Delete a checklist item."""
        self._client.delete(
            f"/me/todo/lists/{list_id}/tasks/{task_id}/checklistItems/{item_id}"
        )

    def close(self) -> None:
        """Close the client."""
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> TasksClient:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()
