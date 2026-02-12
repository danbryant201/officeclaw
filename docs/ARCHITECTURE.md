# Outclaw Architecture

## Package Structure

```
outclaw/
├── pyproject.toml          # Package configuration (PEP 621)
├── src/
│   └── outclaw/
│       ├── __init__.py     # Package entry, version, lazy imports
│       ├── __main__.py     # `python -m outclaw` support
│       ├── cli.py          # Click-based CLI
│       ├── exceptions.py   # Custom exception classes
│       ├── auth.py         # OAuth authentication & token management
│       ├── client.py       # Base Graph API client
│       ├── mail.py         # Mail operations
│       ├── calendar.py     # Calendar operations
│       └── tasks.py        # Task operations
├── tests/
│   ├── conftest.py         # Fixtures and mocks
│   ├── test_cli.py         # CLI tests
│   ├── test_auth.py        # Auth tests
│   └── ...
└── .github/workflows/
    ├── test.yml            # CI testing
    └── publish.yml         # PyPI publishing
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
name = "outclaw"
version = "1.0.0"
requires-python = ">=3.9"

[project.scripts]
outclaw = "outclaw.cli:main"  # Creates `outclaw` command

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["-v", "--cov=src/outclaw"]
```

### CLI Entry Point

The `[project.scripts]` section creates the `outclaw` command:

```bash
# After pip install
outclaw --help
outclaw mail list
outclaw calendar list --start 2026-02-01
```

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
- GitHub Release (published)
- Manual dispatch (for testing)

**Flow:**
```
Build → TestPyPI (prerelease) → PyPI (release) → Verify Installation
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
├── test_cli.py           # CLI command tests
├── test_auth.py          # Token management tests
├── test_mail.py          # Mail client tests
├── test_calendar.py      # Calendar client tests
├── test_tasks.py         # Tasks client tests
└── test_integration.py   # Real API tests (marked)
```

### Key Fixtures

```python
@pytest.fixture
def mock_graph_api():
    """Mock Microsoft Graph API responses."""
    with responses.RequestsMock() as rsps:
        yield rsps

@pytest.fixture
def mock_keyring():
    """Mock system keyring for token storage."""
    with patch("outclaw.auth.keyring") as mock:
        yield mock
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src/outclaw --cov-report=html

# Specific test file
pytest tests/test_cli.py

# Skip slow/integration tests
pytest -m "not slow and not integration"

# Only integration tests (requires real credentials)
OUTCLAW_CLIENT_ID=... pytest -m integration
```

---

## Device Code Flow (Future Enhancement)

### What is Device Code Flow?

OAuth 2.0 flow designed for devices without browsers (TVs, CLIs, IoT):

```
┌─────────────────────────────────────────────────────────────┐
│  User runs: outclaw auth login                              │
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

### Why Device Code Flow?

| Aspect | Auth Code Flow (Current) | Device Code Flow |
|--------|--------------------------|------------------|
| Client Secret | Required | Not required |
| Browser | Opens automatically | User opens manually |
| Headless | ❌ Needs display | ✅ Works via SSH |
| Azure Setup | Complex | Simpler |
| Security | Good | Good |

### MSAL Support

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

### Implementation Plan (v1.1)

1. Add `--device-code` flag to `outclaw auth login`
2. Implement `acquire_token_device_code()` in auth.py
3. Update documentation
4. Test on headless systems (Docker, SSH)

**Note:** Keep current Auth Code Flow as default (works well for desktop users).

---

## Security Model

### Token Storage

```
┌─────────────────────────────────────────┐
│           Token Storage                  │
│                                          │
│  ┌───────────────────────────────────┐  │
│  │  Primary: System Keyring          │  │
│  │  - macOS: Keychain                │  │
│  │  - Windows: Credential Manager    │  │
│  │  - Linux: Secret Service          │  │
│  │  ✅ Encrypted at rest             │  │
│  └───────────────────────────────────┘  │
│                  │                       │
│                  ↓ (if unavailable)      │
│  ┌───────────────────────────────────┐  │
│  │  Fallback: File Storage           │  │
│  │  - Location: ~/.outclaw/          │  │
│  │  - Permissions: 600               │  │
│  │  ⚠️ Encrypted by MSAL              │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### Credential Protection

- **.gitignore**: Comprehensive exclusion of sensitive files
- **No hardcoding**: All credentials from environment/.env
- **Token rotation**: Refresh tokens auto-rotate on use
- **CI secrets**: Stored in GitHub Secrets, never in code
