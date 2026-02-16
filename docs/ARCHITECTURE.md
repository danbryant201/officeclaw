# OfficeClaw Architecture

## Package Structure

```
officeclaw/
├── pyproject.toml          # Package configuration (PEP 621)
├── src/
│   └── officeclaw/
│       ├── __init__.py     # Package entry, version, lazy imports
│       ├── __main__.py     # `python -m officeclaw` support
│       ├── cli.py          # Click-based CLI
│       ├── exceptions.py   # Custom exception classes
│       ├── auth.py         # OAuth authentication & token management
│       ├── auth_flow.py    # Auth code flow (legacy fallback)
│       ├── client.py       # Base Graph API client
│       ├── mail.py         # Mail operations
│       ├── calendar.py     # Calendar operations
│       └── tasks.py        # Task operations
├── skill/
│   └── SKILL.md            # OpenClaw skill manifest
├── tests/
│   ├── conftest.py         # Fixtures and mocks
│   ├── test_cli.py         # CLI tests
│   ├── test_auth.py        # Auth tests
│   └── ...
├── docs/
│   ├── ARCHITECTURE.md     # This file
│   └── logo.png            # OfficeClaw logo
└── .github/workflows/
    ├── test.yml            # CI testing
    └── publish.yml         # PyPI publishing on v* tags
```

---

## Python Packaging (pyproject.toml)

### Why pyproject.toml?

- **PEP 621 compliant**: Modern Python standard
- **Single source of truth**: Dependencies, metadata, tools all in one file
- **Tool configurations**: pytest, ruff, black, mypy settings included
- **Build isolation**: Uses hatchling for reliable builds

### Key Sections

```toml
[project]
name = "officeclaw"
version = "1.0.2"
requires-python = ">=3.9"

[project.scripts]
officeclaw = "officeclaw.cli:main"  # Creates `officeclaw` command

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["-v", "--cov=src/officeclaw"]
```

### CLI Entry Point

The `[project.scripts]` section creates the `officeclaw` command:

```bash
# After pip install
officeclaw --help
officeclaw mail list
officeclaw calendar list --start 2026-02-01
```

---

## Authentication Model

### Dual Auth Mode

OfficeClaw supports two authentication modes:

| Aspect | Device Code Flow (Default) | Auth Code Flow (Legacy) |
|--------|---------------------------|------------------------|
| Client Secret | Not required | Required |
| Browser | User opens manually | Opens automatically |
| Headless | ✅ Works via SSH | ❌ Needs display |
| Azure Setup | Simpler | Complex |
| Activation | Default (no secret set) | Set `OFFICECLAW_CLIENT_SECRET` |

### Default: Device Code Flow

```
┌─────────────────────────────────────────────────────────────┐
│  User runs: officeclaw auth login                           │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  CLI requests device code from Microsoft                    │
│  POST https://login.microsoftonline.com/.../devicecode      │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Microsoft returns:                                          │
│  - device_code: "ABC123..."                                  │
│  - user_code: "ABCD-1234"                                    │
│  - verification_uri: "https://microsoft.com/devicelogin"    │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  CLI displays to user:                                       │
│  "Visit https://microsoft.com/devicelogin                    │
│   and enter code: ABCD-1234"                                 │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
        ┌───────────────────┴───────────────────┐
        ↓                                       ↓
┌───────────────────┐               ┌───────────────────────┐
│ User opens browser │               │ CLI polls Microsoft   │
│ Enters code        │               │ every 5 seconds       │
│ Approves consent   │               │ Waiting for approval  │
└───────────────────┘               └───────────────────────┘
        │                                       │
        └───────────────┬───────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│  Microsoft returns tokens to CLI                             │
│  - access_token                                              │
│  - refresh_token                                             │
└─────────────────────────────────────────────────────────────┘
```

### Default Client ID

OfficeClaw ships with a built-in public client ID (`1db8c9bb-eebf-4eb9-82dc-e3ec91d1ca53`) so users can authenticate immediately without creating their own Azure app registration. Users can override this by setting `OFFICECLAW_CLIENT_ID` in their `.env`.

### MSAL Implementation

```python
from msal import PublicClientApplication

app = PublicClientApplication(client_id)

# Initiate device code flow
flow = app.initiate_device_flow(scopes=["Mail.Read", ...])

print(f"Visit {flow['verification_uri']} and enter: {flow['user_code']}")

# Poll for completion (blocks until user approves or timeout)
result = app.acquire_token_by_device_flow(flow)

# Result contains access_token, refresh_token, etc.
```

---

## Capability Gates

Write operations are disabled by default for safety:

| Gate | Env Var | Commands Protected |
|------|---------|-------------------|
| Send | `OFFICECLAW_ENABLE_SEND=true` | `mail send`, `mail reply`, `mail forward` |
| Delete | `OFFICECLAW_ENABLE_DELETE=true` | `mail delete`, `calendar delete`, `tasks delete` |

Read operations (list, get, search) are always available. This ensures a compromised agent cannot send emails or delete data unless explicitly enabled.

---

## CI/CD Pipeline

### test.yml - Continuous Integration

**Triggers:**
- Push to `main` or `develop`
- Pull requests to `main`

**Jobs:**

1. **Lint & Format**
   - Black (formatting)
   - Ruff (linting)
   - Mypy (type checking)

2. **Security Audit**
   - pip-audit (dependency vulnerabilities)
   - Bandit (code security)
   - TruffleHog (secret scanning)

3. **Test Matrix**
   - Python 3.9, 3.10, 3.11, 3.12
   - pytest with coverage
   - Upload to Codecov

4. **Build Verification**
   - Build wheel and sdist
   - Verify with twine

### publish.yml - Release Publishing

**Triggers:**
- Push tag matching `v*` (e.g. `v1.0.2`)
- Manual dispatch (for testing)

**Flow:**
```
Build → PyPI (via Trusted Publishing) → Verify Installation
```

Uses **Trusted Publishing** (no API tokens needed):
- PyPI verifies GitHub Actions identity
- More secure than storing tokens

---

## Unit Testing Strategy

### Testing Principles

1. **Mock external dependencies**: Never call real APIs in unit tests
2. **Test behavior, not implementation**: Focus on inputs/outputs
3. **Use fixtures**: Consistent test data
4. **Fast by default**: Integration tests are opt-in

### Test Organization

```
tests/
├── conftest.py           # Shared fixtures
│   ├── mock_graph_api    # responses library mock
│   ├── mock_keyring      # Keyring mock
│   ├── sample_*          # Sample data fixtures
├── test_cli.py           # CLI command tests (incl. capability gates)
├── test_auth.py          # Token management tests
├── test_mail.py          # Mail client tests
├── test_calendar.py      # Calendar client tests
└── test_tasks.py         # Tasks client tests
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src/officeclaw --cov-report=html

# Specific test file
pytest tests/test_cli.py

# Skip slow/integration tests
pytest -m "not slow and not integration"

# Only integration tests (requires real credentials)
OFFICECLAW_CLIENT_ID=... pytest -m integration
```

---

## Security Model

### Token Storage

```
┌─────────────────────────────────────────┐
│           Token Storage                  │
│                                          │
│  ┌───────────────────────────────────┐  │
│  │  Primary: MSAL Token Cache        │  │
│  │  - Location: ~/.officeclaw/       │  │
│  │  - File: token_cache.json         │  │
│  │  - Permissions: 600               │  │
│  │  ✅ Serialized by MSAL            │  │
│  └───────────────────────────────────┘  │
│                  │                       │
│                  ↓ (legacy fallback)     │
│  ┌───────────────────────────────────┐  │
│  │  System Keyring                   │  │
│  │  - macOS: Keychain                │  │
│  │  - Windows: Credential Manager    │  │
│  │  - Linux: Secret Service          │  │
│  │  ✅ Encrypted at rest             │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### Credential Protection

- **.gitignore**: Comprehensive exclusion of sensitive files
- **No hardcoded secrets**: All credentials from environment/.env
- **Default client ID**: Public client only (no secret, no risk if exposed)
- **Token rotation**: Refresh tokens auto-rotate on use
- **Capability gates**: Write operations require explicit opt-in
- **CI secrets**: Stored in GitHub Secrets, never in code
