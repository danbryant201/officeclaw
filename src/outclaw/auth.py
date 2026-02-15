"""
Authentication and token management for Outclaw.

Handles OAuth 2.0 token storage, retrieval, and refresh using MSAL.
Supports secure storage via system keyring with file fallback.
"""

from __future__ import annotations

import contextlib
import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from msal import ConfidentialClientApplication

from outclaw.exceptions import AuthenticationError, ConfigurationError, TokenStorageError

# Optional keyring support
try:
    import keyring

    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False


class TokenManager:
    """
    Manages OAuth tokens for Microsoft Graph API access.

    Features:
        - Secure storage using system keyring (with file fallback)
        - Automatic token refresh when expired
        - In-memory caching for performance
        - Thread-safe token access

    Example:
        manager = TokenManager()
        token = manager.get_access_token()
    """

    KEYRING_SERVICE = "outclaw"
    LEGACY_KEYRING_SERVICE = "out-claw"
    KEYRING_USERNAME = "microsoft-graph-tokens"

    DEFAULT_SCOPES = [
        "Mail.Read",
        "Mail.ReadWrite",
        "Mail.Send",
        "Calendars.Read",
        "Calendars.ReadWrite",
        "Tasks.ReadWrite",
    ]

    def __init__(self) -> None:
        """Initialize token manager with configuration from environment."""
        load_dotenv()

        # Load configuration
        self.client_id = os.getenv("OUTCLAW_CLIENT_ID")
        self.client_secret = os.getenv("OUTCLAW_CLIENT_SECRET")
        self.tenant_id = os.getenv("OUTCLAW_TENANT_ID", "consumers")
        self.redirect_uri = os.getenv("OUTCLAW_REDIRECT_URI", "http://localhost:8000/callback")

        scopes_str = os.getenv("OUTCLAW_SCOPES")
        self.scopes = scopes_str.split() if scopes_str else self.DEFAULT_SCOPES

        self.use_keyring = os.getenv("OUTCLAW_USE_KEYRING", "true").lower() == "true"
        self.token_refresh_threshold = int(os.getenv("OUTCLAW_TOKEN_REFRESH_THRESHOLD", "300"))

        # Validate required configuration
        if not self.client_id:
            raise ConfigurationError(
                "OUTCLAW_CLIENT_ID is required. " "Set it in .env or as an environment variable."
            )

        if not self.client_secret:
            raise ConfigurationError(
                "OUTCLAW_CLIENT_SECRET is required. "
                "Set it in .env or as an environment variable."
            )

        # Token storage directory
        cache_dir = os.getenv("OUTCLAW_TOKEN_CACHE_DIR", ".outclaw")
        self.token_dir = Path.home() / cache_dir
        self.token_dir.mkdir(mode=0o700, exist_ok=True)

        cache_file = os.getenv("OUTCLAW_TOKEN_CACHE_FILE", "token_cache.json")
        self.token_file = self.token_dir / cache_file

        # Build authority URL
        authority_base = os.getenv("OUTCLAW_AUTHORITY", "https://login.microsoftonline.com")
        self.authority = f"{authority_base}/{self.tenant_id}"

        # Initialize MSAL app
        self._app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority,
        )

        # In-memory cache
        self._cached_tokens: dict[str, Any] | None = None
        self._cache_time: float | None = None

    def save_tokens(self, tokens: dict[str, Any]) -> None:
        """
        Save tokens securely.

        Args:
            tokens: Token dictionary from MSAL
        """
        token_data = {
            **tokens,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "scopes": self.scopes,
        }

        # Try keyring first
        if self.use_keyring and KEYRING_AVAILABLE:
            try:
                keyring.set_password(
                    self.KEYRING_SERVICE,
                    self.KEYRING_USERNAME,
                    json.dumps(token_data),
                )
                self._update_cache(token_data)
                return
            except Exception:  # noqa: S110
                pass  # Fall through to file storage

        # File fallback
        self._save_to_file(token_data)
        self._update_cache(token_data)

    def _save_to_file(self, tokens: dict[str, Any]) -> None:
        """Save tokens to file with secure permissions."""
        try:
            with open(self.token_file, "w") as f:
                json.dump(tokens, f, indent=2)
            os.chmod(self.token_file, 0o600)
        except OSError as e:
            raise TokenStorageError(f"Failed to save tokens: {e}") from e

    def _update_cache(self, tokens: dict[str, Any]) -> None:
        """Update in-memory token cache."""
        self._cached_tokens = tokens
        self._cache_time = time.time()

    def get_tokens(self) -> dict[str, Any] | None:
        """
        Retrieve stored tokens.

        Returns:
            Token dictionary or None if no tokens found
        """
        # Check in-memory cache (valid for 60 seconds)
        if self._cached_tokens and self._cache_time and time.time() - self._cache_time < 60:
            return self._cached_tokens

        # Try keyring (current service name, then legacy "out-claw" fallback)
        if self.use_keyring and KEYRING_AVAILABLE:
            for service in (self.KEYRING_SERVICE, self.LEGACY_KEYRING_SERVICE):
                try:
                    token_json = keyring.get_password(
                        service,
                        self.KEYRING_USERNAME,
                    )
                    if token_json:
                        tokens = json.loads(token_json)
                        # Migrate legacy tokens to new service name
                        if service == self.LEGACY_KEYRING_SERVICE:
                            self.save_tokens(tokens)
                        else:
                            self._update_cache(tokens)
                        return tokens
                except Exception:  # noqa: S110, S112
                    continue

        # Try file storage
        if self.token_file.exists():
            try:
                with open(self.token_file) as f:
                    tokens = json.load(f)
                self._update_cache(tokens)
                return tokens
            except Exception as e:
                raise TokenStorageError(f"Failed to read tokens: {e}") from e

        return None

    def get_access_token(self) -> str:
        """
        Get a valid access token, refreshing if necessary.

        Returns:
            Valid access token string

        Raises:
            AuthenticationError: If no tokens found or refresh fails
        """
        tokens = self.get_tokens()

        if not tokens:
            raise AuthenticationError(
                "No authentication tokens found. " "Run 'outclaw auth login' to authenticate."
            )

        if self._needs_refresh(tokens):
            tokens = self._refresh_tokens(tokens)

        return tokens["access_token"]

    def _needs_refresh(self, tokens: dict[str, Any]) -> bool:
        """Check if access token needs to be refreshed."""
        if "expires_in" not in tokens or "saved_at" not in tokens:
            return True

        saved_at = datetime.fromisoformat(tokens["saved_at"].replace("Z", "+00:00"))
        expires_in = tokens["expires_in"]
        expires_at = saved_at + timedelta(seconds=expires_in)

        threshold = timedelta(seconds=self.token_refresh_threshold)
        return datetime.now(timezone.utc) >= (expires_at - threshold)

    def _refresh_tokens(self, tokens: dict[str, Any]) -> dict[str, Any]:
        """
        Refresh access token using refresh token.

        Args:
            tokens: Current token dictionary

        Returns:
            New token dictionary

        Raises:
            AuthenticationError: If refresh fails
        """
        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            raise AuthenticationError(
                "No refresh token available. " "Run 'outclaw auth login' to re-authenticate."
            )

        try:
            result = self._app.acquire_token_by_refresh_token(
                refresh_token=refresh_token,
                scopes=self.scopes,
            )

            if "error" in result:
                error_desc = result.get("error_description", result["error"])
                raise AuthenticationError(f"Token refresh failed: {error_desc}")

            if "access_token" not in result:
                raise AuthenticationError("No access token in refresh response")

            self.save_tokens(result)
            return result

        except AuthenticationError:
            raise
        except Exception as e:
            raise AuthenticationError(f"Failed to refresh token: {e}") from e

    def clear_tokens(self) -> None:
        """Clear all stored tokens (logout)."""
        # Clear keyring
        if self.use_keyring and KEYRING_AVAILABLE:
            with contextlib.suppress(Exception):
                keyring.delete_password(self.KEYRING_SERVICE, self.KEYRING_USERNAME)

        # Clear file
        if self.token_file.exists():
            with contextlib.suppress(Exception):
                self.token_file.unlink()

        # Clear cache
        self._cached_tokens = None
        self._cache_time = None

    def get_token_info(self) -> dict[str, Any] | None:
        """
        Get information about stored tokens (for status display).

        Returns:
            Token metadata (no sensitive values) or None
        """
        tokens = self.get_tokens()
        if not tokens:
            return None

        saved_at_str = tokens.get("saved_at", "1970-01-01T00:00:00+00:00")
        saved_at = datetime.fromisoformat(saved_at_str.replace("Z", "+00:00"))
        expires_in = tokens.get("expires_in", 0)
        expires_at = saved_at + timedelta(seconds=expires_in)
        time_until_expiry = expires_at - datetime.now(timezone.utc)

        storage_location = (
            f"System keyring ({self.KEYRING_SERVICE})"
            if self.use_keyring and KEYRING_AVAILABLE
            else str(self.token_file)
        )

        return {
            "saved_at": saved_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "expires_in_seconds": expires_in,
            "time_until_expiry_seconds": int(time_until_expiry.total_seconds()),
            "is_expired": time_until_expiry.total_seconds() <= 0,
            "needs_refresh": self._needs_refresh(tokens),
            "scopes": tokens.get("scope", "").split() if tokens.get("scope") else [],
            "storage_location": storage_location,
        }

    @property
    def is_authenticated(self) -> bool:
        """Check if valid tokens exist."""
        tokens = self.get_tokens()
        return tokens is not None and "access_token" in tokens
