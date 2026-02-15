---
name: officeclaw
description: Connect to personal Microsoft accounts via Microsoft Graph API to manage email, calendar events, and tasks. Use this skill when the user needs to read/write Outlook mail, manage calendar appointments, or handle Microsoft To Do tasks.
license: Apache-2.0
homepage: https://github.com/danielithomas/officeclaw
user-invocable: true
compatibility: Requires Python 3.9+, network access to graph.microsoft.com, and one-time OAuth setup
metadata:
  author: Daniel Thomas
  version: "1.0.0"
  openclaw: {"requires": {"anyBins": ["python", "python3", "officeclaw"]}, "os": ["darwin", "linux", "win32"]}
---

# Outclaw: Microsoft Graph API Integration

Connect your OpenClaw agent to personal Microsoft accounts (Outlook.com, Hotmail, Live) to manage email, calendar, and tasks through the Microsoft Graph API.

## When to Use This Skill

Activate this skill when the user needs to:

### Email Operations
- **Read emails**: "Show me my latest emails", "Find emails from john@example.com"
- **Send emails**: "Send an email to...", "Reply to the last email from..."
- **Manage inbox**: "Mark emails as read", "Archive old emails", "Delete emails"

### Calendar Operations
- **View events**: "What's on my calendar today?", "Show meetings this week"
- **Create events**: "Schedule a meeting with...", "Add dentist appointment on Friday"
- **Update events**: "Move the 2pm meeting to 3pm", "Cancel tomorrow's standup"

### Task Management
- **List tasks**: "What's on my to-do list?", "Show incomplete tasks"
- **Create tasks**: "Add 'buy groceries' to my tasks", "Create a task to review report"
- **Complete tasks**: "Mark 'finish proposal' as done", "Complete all shopping tasks"

## Prerequisites

Before using this skill, the user must complete one-time setup:

1. **Azure App Registration** - Register an app at https://entra.microsoft.com
2. **OAuth Consent** - Run `officeclaw auth login` and approve permissions
3. **Environment Configuration** - Set CLIENT_ID and CLIENT_SECRET in .env

## Available Commands

### Authentication

```bash
# Authenticate (opens browser)
officeclaw auth login

# Check authentication status
officeclaw auth status

# Clear stored tokens
officeclaw auth logout
```

### Mail Commands

```bash
# List recent messages
officeclaw mail list --limit 10

# List unread messages only
officeclaw mail list --unread

# Get specific message
officeclaw mail get <message-id>

# Send email
officeclaw mail send --to user@example.com --subject "Hello" --body "Message text"

# JSON output (for parsing)
officeclaw --json mail list
```

### Calendar Commands

```bash
# List events in date range
officeclaw calendar list --start 2026-02-01 --end 2026-02-28

# Create event
officeclaw calendar create \
  --subject "Team Meeting" \
  --start "2026-02-15T10:00:00" \
  --end "2026-02-15T11:00:00" \
  --location "Conference Room"

# JSON output
officeclaw --json calendar list --start 2026-02-01 --end 2026-02-28
```

### Task Commands

```bash
# List task lists
officeclaw tasks list-lists

# List tasks in a list
officeclaw tasks list --list-id <list-id>

# List only active (not completed) tasks
officeclaw tasks list --list-id <list-id> --status active

# Create task
officeclaw tasks create --list-id <list-id> --title "Complete report" --due-date "2026-02-20"

# Mark task complete
officeclaw tasks complete --list-id <list-id> --task-id <task-id>

# Reopen a completed task
officeclaw tasks reopen --list-id <list-id> --task-id <task-id>
```

## Output Format

Use `--json` flag for structured JSON output:

```bash
officeclaw --json mail list
```

Returns:
```json
{
  "status": "success",
  "data": [
    {
      "id": "AAMkADEzN...",
      "subject": "Meeting Notes",
      "from": {"emailAddress": {"address": "sender@example.com"}},
      "receivedDateTime": "2026-02-12T10:30:00Z",
      "isRead": false
    }
  ]
}
```

## Error Handling

Common errors and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| `AuthenticationError` | Not logged in or token expired | Run `officeclaw auth login` |
| `AccessDenied` | Missing permissions | Re-authenticate with required scopes |
| `ResourceNotFound` | Invalid ID | Verify the ID exists |
| `RateLimitError` | Too many API calls | Wait 60 seconds and retry |

## Guidelines for Agents

When using this skill:

1. **Confirm destructive actions**: Ask before deleting or sending
2. **Summarize results**: Don't show raw JSON, provide summaries
3. **Handle errors gracefully**: Guide user through re-authentication
4. **Respect privacy**: Don't log email content
5. **Use JSON mode**: For programmatic parsing, use `--json` flag
6. **Batch operations**: Process multiple items efficiently

## Example Agent Interactions

### Example 1: Check for urgent emails

```
User: "Do I have any urgent emails?"
Agent: I'll check your inbox.
[Runs: officeclaw --json mail list --limit 20]
Agent: You have 2 unread emails:
       • From your manager about tomorrow's deadline
       • From IT about a password reset
```

### Example 2: Schedule a meeting

```
User: "Schedule a meeting with john@example.com tomorrow at 2pm for 1 hour"
Agent: I'll create that calendar event.
[Runs: officeclaw calendar create --subject "Meeting with John" 
       --start "2026-02-13T14:00:00" --end "2026-02-13T15:00:00"]
Agent: Meeting scheduled for tomorrow at 2:00 PM.
```

### Example 3: Complete a task

```
User: "Mark the 'finish slides' task as complete"
Agent: I'll mark that task as done.
[Runs: officeclaw --json tasks list --list-id <id>]
[Runs: officeclaw tasks complete --list-id <id> --task-id <id>]
Agent: Done! "Finish slides" has been marked as complete.
```

## Security & Privacy

- **Tokens stored securely**: System keyring or encrypted file
- **No data storage**: Outclaw passes data through, never stores content
- **No telemetry**: No usage data collected
- **Least privilege**: Only requests necessary permissions

## Troubleshooting

If the skill isn't working:

1. **Check authentication**: Run `officeclaw auth status`
2. **Re-authenticate**: Run `officeclaw auth login`
3. **Verify network**: Ensure `graph.microsoft.com` is reachable
4. **Check environment**: Verify OUTCLAW_CLIENT_ID is set

## References

- [Outclaw Documentation](https://github.com/danielithomas/officeclaw)
- [Microsoft Graph API](https://docs.microsoft.com/graph/)
- [OpenClaw](https://docs.openclaw.ai)
