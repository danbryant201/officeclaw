"""
Outclaw - Microsoft Graph API integration for OpenClaw agents.

Provides email, calendar, and task management through a simple CLI
and Python API.

Example usage:
    # CLI
    $ outclaw mail list --limit 10
    $ outclaw calendar list --start 2026-02-01 --end 2026-02-28
    $ outclaw tasks list-lists

    # Python
    from outclaw import MailClient, CalendarClient, TasksClient

    mail = MailClient()
    messages = mail.list_messages(limit=10)
"""

__version__ = "1.0.0"
__author__ = "Daniel Thomas"
__email__ = "dan@theenquiringmind.com"


# Lazy imports to avoid loading everything on import
def __getattr__(name: str):
    """Lazy import of client classes."""
    if name == "MailClient":
        from outclaw.mail import MailClient

        return MailClient
    elif name == "CalendarClient":
        from outclaw.calendar import CalendarClient

        return CalendarClient
    elif name == "TasksClient":
        from outclaw.tasks import TasksClient

        return TasksClient
    elif name == "TokenManager":
        from outclaw.auth import TokenManager

        return TokenManager
    elif name == "GraphClient":
        from outclaw.client import GraphClient

        return GraphClient
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "__version__",
    "MailClient",
    "CalendarClient",
    "TasksClient",
    "TasksClient",
    "TokenManager",
    "GraphClient",
]
