"""
Outclaw CLI - Command-line interface for Microsoft Graph API.

Provides mail, calendar, and task operations for OpenClaw agents.

Usage:
    outclaw mail list --limit 10
    outclaw calendar list --start 2026-02-01 --end 2026-02-28
    outclaw tasks list-lists
"""

from __future__ import annotations

import json
import sys
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from outclaw import __version__
from outclaw.auth import TokenManager
from outclaw.client import GraphClient
from outclaw.exceptions import AuthenticationError, GraphAPIError, OutclawError

# Rich console for pretty output
console = Console()
error_console = Console(stderr=True)


def output_json(data: Any, status: str = "success") -> None:
    """Output data as JSON."""
    response = {"status": status}
    if status == "success":
        response["data"] = data
    else:
        response["error"] = data
    click.echo(json.dumps(response, indent=2, default=str))


def handle_error(e: Exception) -> None:
    """Handle and display errors."""
    if isinstance(e, AuthenticationError):
        error_console.print(f"[red]Authentication Error:[/red] {e}")
        error_console.print("Run [bold]outclaw auth login[/bold] to authenticate.")
    elif isinstance(e, GraphAPIError):
        error_console.print(f"[red]API Error ({e.code}):[/red] {e.message}")
    elif isinstance(e, OutclawError):
        error_console.print(f"[red]Error:[/red] {e}")
    else:
        error_console.print(f"[red]Unexpected Error:[/red] {e}")
    sys.exit(1)


# ============================================
# MAIN CLI GROUP
# ============================================


@click.group()
@click.version_option(version=__version__, prog_name="outclaw")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def main(ctx: click.Context, json_output: bool) -> None:
    """
    Outclaw - Microsoft Graph API integration for OpenClaw.

    Manage email, calendar, and tasks from your personal Microsoft account.
    """
    ctx.ensure_object(dict)
    ctx.obj["json"] = json_output


# ============================================
# AUTH COMMANDS
# ============================================


@main.group()
def auth() -> None:
    """Authentication commands."""
    pass


@auth.command()
def login() -> None:
    """Authenticate with Microsoft (opens browser)."""
    try:
        # Import here to avoid circular imports
        from outclaw.auth_flow import run_auth_flow

        run_auth_flow()
    except ImportError:
        error_console.print("[yellow]Auth flow not yet implemented.[/yellow]")
        error_console.print("Please run the auth setup script manually.")
        sys.exit(1)
    except Exception as e:
        handle_error(e)


@auth.command()
def logout() -> None:
    """Clear stored authentication tokens."""
    try:
        manager = TokenManager()
        manager.clear_tokens()
        console.print("[green]✓[/green] Logged out successfully.")
    except Exception as e:
        handle_error(e)


@auth.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show authentication status."""
    try:
        manager = TokenManager()
        info = manager.get_token_info()

        if ctx.obj.get("json"):
            output_json(info)
            return

        if not info:
            console.print("[yellow]Not authenticated.[/yellow]")
            console.print("Run [bold]outclaw auth login[/bold] to authenticate.")
            return

        table = Table(title="Authentication Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value")

        status_emoji = "🔴" if info["is_expired"] else "🟢"
        table.add_row("Status", f"{status_emoji} {'Expired' if info['is_expired'] else 'Valid'}")
        table.add_row("Expires", info["expires_at"])
        table.add_row("Time Left", f"{info['time_until_expiry_seconds']}s")
        table.add_row("Needs Refresh", "Yes" if info["needs_refresh"] else "No")
        table.add_row("Storage", info["storage_location"])
        table.add_row(
            "Scopes", ", ".join(info["scopes"][:3]) + ("..." if len(info["scopes"]) > 3 else "")
        )

        console.print(table)

    except Exception as e:
        handle_error(e)


# ============================================
# MAIL COMMANDS
# ============================================


@main.group()
def mail() -> None:
    """Email operations."""
    pass


@mail.command("list")
@click.option("--limit", default=10, help="Number of messages to return")
@click.option("--folder", default="inbox", help="Mail folder")
@click.option("--unread", is_flag=True, help="Only unread messages")
@click.pass_context
def mail_list(ctx: click.Context, limit: int, folder: str, unread: bool) -> None:
    """List email messages."""
    try:
        with GraphClient() as client:
            params: dict[str, Any] = {
                "$top": limit,
                "$orderby": "receivedDateTime desc",
                "$select": "id,subject,from,receivedDateTime,isRead,importance",
            }
            if unread:
                params["$filter"] = "isRead eq false"

            endpoint = f"/me/mailFolders/{folder}/messages"
            messages = client.get_all(endpoint, params=params, limit=limit)

            if ctx.obj.get("json"):
                output_json(messages)
                return

            if not messages:
                console.print("[yellow]No messages found.[/yellow]")
                return

            table = Table(title=f"Messages ({folder})")
            table.add_column("From", style="cyan", max_width=25)
            table.add_column("Subject", max_width=40)
            table.add_column("Date", style="dim")
            table.add_column("Read")

            for msg in messages:
                from_addr = msg.get("from", {}).get("emailAddress", {})
                from_name = from_addr.get("name", from_addr.get("address", "Unknown"))
                subject = msg.get("subject", "(No subject)")[:40]
                date = msg.get("receivedDateTime", "")[:10]
                is_read = "✓" if msg.get("isRead") else "•"

                table.add_row(from_name[:25], subject, date, is_read)

            console.print(table)

    except Exception as e:
        handle_error(e)


@mail.command("get")
@click.argument("message_id")
@click.pass_context
def mail_get(ctx: click.Context, message_id: str) -> None:
    """Get a specific email message."""
    try:
        with GraphClient() as client:
            message = client.get(f"/me/messages/{message_id}")

            if ctx.obj.get("json"):
                output_json(message)
                return

            console.print(f"[bold]Subject:[/bold] {message.get('subject')}")
            console.print(
                f"[bold]From:[/bold] {message.get('from', {}).get('emailAddress', {}).get('address')}"
            )
            console.print(f"[bold]Date:[/bold] {message.get('receivedDateTime')}")
            console.print()
            console.print(message.get("bodyPreview", ""))

    except Exception as e:
        handle_error(e)


@mail.command("send")
@click.option("--to", required=True, help="Recipient email address")
@click.option("--subject", required=True, help="Email subject")
@click.option("--body", required=True, help="Email body")
@click.pass_context
def mail_send(ctx: click.Context, to: str, subject: str, body: str) -> None:
    """Send an email message."""
    try:
        with GraphClient() as client:
            message = {
                "message": {
                    "subject": subject,
                    "body": {"contentType": "Text", "content": body},
                    "toRecipients": [{"emailAddress": {"address": to}}],
                },
                "saveToSentItems": True,
            }
            client.post("/me/sendMail", message)

            if ctx.obj.get("json"):
                output_json({"sent": True, "to": to, "subject": subject})
            else:
                console.print(f"[green]✓[/green] Email sent to {to}")

    except Exception as e:
        handle_error(e)


# ============================================
# CALENDAR COMMANDS
# ============================================


@main.group()
def calendar() -> None:
    """Calendar operations."""
    pass


@calendar.command("list")
@click.option("--start", required=True, help="Start date (YYYY-MM-DD)")
@click.option("--end", required=True, help="End date (YYYY-MM-DD)")
@click.option("--limit", default=50, help="Maximum events")
@click.pass_context
def calendar_list(ctx: click.Context, start: str, end: str, limit: int) -> None:
    """List calendar events in date range."""
    try:
        with GraphClient() as client:
            params = {
                "startDateTime": f"{start}T00:00:00Z",
                "endDateTime": f"{end}T23:59:59Z",
                "$top": limit,
                "$orderby": "start/dateTime",
                "$select": "id,subject,start,end,location,isAllDay",
            }
            events = client.get_all("/me/calendarView", params=params, limit=limit)

            if ctx.obj.get("json"):
                output_json(events)
                return

            if not events:
                console.print("[yellow]No events found.[/yellow]")
                return

            table = Table(title=f"Events ({start} to {end})")
            table.add_column("Date", style="cyan")
            table.add_column("Time")
            table.add_column("Subject", max_width=35)
            table.add_column("Location", max_width=20)

            for event in events:
                start_dt = event.get("start", {}).get("dateTime", "")
                date = start_dt[:10] if start_dt else ""
                time_str = start_dt[11:16] if start_dt else ""
                subject = event.get("subject", "")[:35]
                location = (event.get("location", {}).get("displayName", "") or "")[:20]

                table.add_row(date, time_str, subject, location)

            console.print(table)

    except Exception as e:
        handle_error(e)


@calendar.command("create")
@click.option("--subject", required=True, help="Event subject")
@click.option("--start", required=True, help="Start datetime (YYYY-MM-DDTHH:MM:SS)")
@click.option("--end", required=True, help="End datetime (YYYY-MM-DDTHH:MM:SS)")
@click.option("--location", default="", help="Event location")
@click.pass_context
def calendar_create(ctx: click.Context, subject: str, start: str, end: str, location: str) -> None:
    """Create a calendar event."""
    try:
        with GraphClient() as client:
            event = {
                "subject": subject,
                "start": {"dateTime": start, "timeZone": "UTC"},
                "end": {"dateTime": end, "timeZone": "UTC"},
            }
            if location:
                event["location"] = {"displayName": location}

            result = client.post("/me/events", event)

            if ctx.obj.get("json"):
                output_json(result)
            else:
                console.print(f"[green]✓[/green] Event created: {subject}")

    except Exception as e:
        handle_error(e)


# ============================================
# TASKS COMMANDS
# ============================================


@main.group()
def tasks() -> None:
    """Task operations (Microsoft To Do)."""
    pass


@tasks.command("list-lists")
@click.pass_context
def tasks_list_lists(ctx: click.Context) -> None:
    """List all task lists."""
    try:
        with GraphClient() as client:
            lists = client.get_all("/me/todo/lists")

            if ctx.obj.get("json"):
                output_json(lists)
                return

            if not lists:
                console.print("[yellow]No task lists found.[/yellow]")
                return

            table = Table(title="Task Lists")
            table.add_column("Name", style="cyan")
            table.add_column("ID", style="dim", max_width=20)

            for lst in lists:
                name = lst.get("displayName", "")
                list_id = lst.get("id", "")[:20]
                table.add_row(name, list_id + "...")

            console.print(table)

    except Exception as e:
        handle_error(e)


@tasks.command("list")
@click.option("--list-id", required=True, help="Task list ID")
@click.option("--status", type=click.Choice(["all", "active", "completed"]), default="all")
@click.pass_context
def tasks_list(ctx: click.Context, list_id: str, status: str) -> None:
    """List tasks in a task list."""
    try:
        with GraphClient() as client:
            params: dict[str, Any] = {
                "$select": "id,title,status,importance,dueDateTime",
            }
            if status == "active":
                params["$filter"] = "status ne 'completed'"
            elif status == "completed":
                params["$filter"] = "status eq 'completed'"

            tasks_list = client.get_all(f"/me/todo/lists/{list_id}/tasks", params=params)

            if ctx.obj.get("json"):
                output_json(tasks_list)
                return

            if not tasks_list:
                console.print("[yellow]No tasks found.[/yellow]")
                return

            table = Table(title="Tasks")
            table.add_column("Status")
            table.add_column("Title", max_width=40)
            table.add_column("Due", style="dim")

            for task in tasks_list:
                task_status = "✓" if task.get("status") == "completed" else "○"
                title = task.get("title", "")[:40]
                due = (
                    task.get("dueDateTime", {}).get("dateTime", "")[:10]
                    if task.get("dueDateTime")
                    else ""
                )

                table.add_row(task_status, title, due)

            console.print(table)

    except Exception as e:
        handle_error(e)


@tasks.command("create")
@click.option("--list-id", required=True, help="Task list ID")
@click.option("--title", required=True, help="Task title")
@click.option("--due-date", default=None, help="Due date (YYYY-MM-DD)")
@click.pass_context
def tasks_create(ctx: click.Context, list_id: str, title: str, due_date: str | None) -> None:
    """Create a new task."""
    try:
        with GraphClient() as client:
            task: dict[str, Any] = {"title": title}
            if due_date:
                task["dueDateTime"] = {
                    "dateTime": f"{due_date}T00:00:00.0000000",
                    "timeZone": "UTC",
                }

            result = client.post(f"/me/todo/lists/{list_id}/tasks", task)

            if ctx.obj.get("json"):
                output_json(result)
            else:
                console.print(f"[green]✓[/green] Task created: {title}")

    except Exception as e:
        handle_error(e)


@tasks.command("complete")
@click.option("--list-id", required=True, help="Task list ID")
@click.option("--task-id", required=True, help="Task ID")
@click.pass_context
def tasks_complete(ctx: click.Context, list_id: str, task_id: str) -> None:
    """Mark a task as completed."""
    try:
        from datetime import datetime, timezone

        with GraphClient() as client:
            completed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.0000000Z")
            data = {
                "status": "completed",
                "completedDateTime": {
                    "dateTime": completed_at,
                    "timeZone": "UTC",
                },
            }
            result = client.patch(f"/me/todo/lists/{list_id}/tasks/{task_id}", data)

            if ctx.obj.get("json"):
                output_json(result)
            else:
                console.print("[green]✓[/green] Task marked as completed.")

    except Exception as e:
        handle_error(e)


@tasks.command("reopen")
@click.option("--list-id", required=True, help="Task list ID")
@click.option("--task-id", required=True, help="Task ID")
@click.pass_context
def tasks_reopen(ctx: click.Context, list_id: str, task_id: str) -> None:
    """Reopen a completed task."""
    try:
        with GraphClient() as client:
            data = {
                "status": "notStarted",
                "completedDateTime": None,
            }
            result = client.patch(f"/me/todo/lists/{list_id}/tasks/{task_id}", data)

            if ctx.obj.get("json"):
                output_json(result)
            else:
                console.print("[green]✓[/green] Task reopened.")

    except Exception as e:
        handle_error(e)


if __name__ == "__main__":
    main()
