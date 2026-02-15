<p align="center">
  <img src="docs/logo.png" alt="OfficeClaw" width="200">
</p>

<h1 align="center">OfficeClaw</h1>

<p align="center">
  <em>Microsoft Graph API integration for OpenClaw agents — manage email, calendar, and tasks.</em>
</p>

[![PyPI](https://img.shields.io/pypi/v/officeclaw.svg)](https://pypi.org/project/officeclaw/)
[![Python](https://img.shields.io/pypi/pyversions/officeclaw.svg)](https://pypi.org/project/officeclaw/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

## Overview

**Officeclaw** is an [OpenClaw](https://docs.openclaw.ai) skill that enables AI agents to interact with personal Microsoft accounts through the Microsoft Graph API. Agents can read/write emails, manage calendar events, and handle tasks — all through natural language commands.

### What Can Officeclaw Do?

- 📧 **Email** — Read inbox, send emails, mark read/unread, archive
- 📅 **Calendar** — View events, create meetings, manage appointments  
- ✅ **Tasks** — Manage Microsoft To Do lists, create/complete tasks

## Quick Start

### Installation

```bash
pip install officeclaw
```

### Setup

1. **Create Azure App Registration** (one-time setup)
   
   See [docs/setup.md](docs/setup.md) for detailed instructions.

2. **Configure credentials**

   ```bash
   # Create .env file
   cp .env.template .env
   
   # Edit with your Azure app credentials
   OFFICECLAW_CLIENT_ID=your-client-id
   OFFICECLAW_CLIENT_SECRET=your-client-secret
   ```

3. **Authenticate**

   ```bash
   officeclaw auth login
   ```

### Usage

```bash
# List recent emails
officeclaw mail list --limit 10

# View calendar
officeclaw calendar list --start 2026-02-01 --end 2026-02-28

# List task lists
officeclaw tasks list-lists

# Create a task
officeclaw tasks create --list-id <id> --title "Review report"

# JSON output (for agents)
officeclaw --json mail list
```

## For OpenClaw Agents

Once installed, OpenClaw agents can use Officeclaw through natural language:

```
User: "Show me today's calendar"
Agent: [Uses Officeclaw]
       You have 3 events today:
       - 9:00 AM: Team standup
       - 2:00 PM: Client call
       - 4:00 PM: Project review

User: "Add 'finish report' to my tasks"
Agent: [Uses Officeclaw]
       ✓ Task created: finish report
```

See [skill/SKILL.md](skill/SKILL.md) for the full skill manifest.

## Commands

### Authentication

| Command | Description |
|---------|-------------|
| `officeclaw auth login` | Authenticate with Microsoft |
| `officeclaw auth logout` | Clear stored tokens |
| `officeclaw auth status` | Show authentication status |

### Email

| Command | Description |
|---------|-------------|
| `officeclaw mail list` | List messages |
| `officeclaw mail get <id>` | Get message details |
| `officeclaw mail send --to <email> --subject <subj> --body <body>` | Send email |

### Calendar

| Command | Description |
|---------|-------------|
| `officeclaw calendar list --start <date> --end <date>` | List events |
| `officeclaw calendar create --subject <subj> --start <dt> --end <dt>` | Create event |

### Tasks

| Command | Description |
|---------|-------------|
| `officeclaw tasks list-lists` | List task lists |
| `officeclaw tasks list --list-id <id>` | List tasks |
| `officeclaw tasks create --list-id <id> --title <title>` | Create task |
| `officeclaw tasks complete --list-id <id> --task-id <id>` | Complete task |
| `officeclaw tasks reopen --list-id <id> --task-id <id>` | Reopen task |

## Configuration

Environment variables (or `.env` file):

| Variable | Required | Description |
|----------|----------|-------------|
| `OFFICECLAW_CLIENT_ID` | Yes | Azure app client ID |
| `OFFICECLAW_CLIENT_SECRET` | Yes | Azure app client secret |
| `OFFICECLAW_REDIRECT_URI` | No | Redirect URI (default: `http://localhost:8000/callback`) |
| `OFFICECLAW_TENANT_ID` | No | Tenant ID (default: `consumers`) |

## Security

- **Tokens stored securely** — System keyring (macOS Keychain, Windows Credential Manager) or encrypted file
- **No data storage** — Officeclaw passes data through, never stores emails/events
- **No telemetry** — No usage data collected

See [SECURITY.md](SECURITY.md) for full security documentation.

## Development

```bash
# Clone and install
git clone https://github.com/danielithomas/officeclaw.git
cd officeclaw
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/ tests/
black --check src/ tests/
```

## License

Apache License 2.0 — see [LICENSE](LICENSE)

## Links

- [Documentation](docs/)
- [OpenClaw](https://docs.openclaw.ai)
- [Microsoft Graph API](https://docs.microsoft.com/graph/)
