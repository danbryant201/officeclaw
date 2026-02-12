"""
Tests for the Outclaw auth module.
"""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, mock_open

import pytest

from outclaw.exceptions import AuthenticationError, ConfigurationError


class TestTokenManager:
    """Test TokenManager operations."""

    @patch.dict("os.environ", {
        "OUTCLAW_CLIENT_ID": "test-client-id",
        "OUTCLAW_CLIENT_SECRET": "test-client-secret",
    })
    @patch("outclaw.auth.ConfidentialClientApplication")
    def test_init_with_valid_config(self, mock_app):
        """Test initialization with valid configuration."""
        from outclaw.auth import TokenManager

        manager = TokenManager()

        assert manager.client_id == "test-client-id"
        assert manager.client_secret == "test-client-secret"
        assert manager.tenant_id == "consumers"

    @patch.dict("os.environ", {"OUTCLAW_CLIENT_SECRET": "secret"}, clear=True)
    def test_init_missing_client_id(self):
        """Test initialization fails without client ID."""
        from outclaw.auth import TokenManager

        with pytest.raises(ConfigurationError) as exc_info:
            TokenManager()

        assert "OUTCLAW_CLIENT_ID" in str(exc_info.value)

    @patch.dict("os.environ", {"OUTCLAW_CLIENT_ID": "id"}, clear=True)
    def test_init_missing_client_secret(self):
        """Test initialization fails without client secret."""
        from outclaw.auth import TokenManager

        with pytest.raises(ConfigurationError) as exc_info:
            TokenManager()

        assert "OUTCLAW_CLIENT_SECRET" in str(exc_info.value)

    @patch.dict("os.environ", {
        "OUTCLAW_CLIENT_ID": "test-id",
        "OUTCLAW_CLIENT_SECRET": "test-secret",
    })
    @patch("outclaw.auth.ConfidentialClientApplication")
    @patch("outclaw.auth.KEYRING_AVAILABLE", False)
    def test_save_tokens_to_file(self, mock_app, tmp_path):
        """Test saving tokens to file when keyring unavailable."""
        from outclaw.auth import TokenManager

        with patch.object(TokenManager, "token_dir", tmp_path):
            manager = TokenManager()
            manager.token_file = tmp_path / "tokens.json"

            tokens = {
                "access_token": "test-access-token",
                "refresh_token": "test-refresh-token",
                "expires_in": 3600,
            }

            manager.save_tokens(tokens)

            # Verify file was created
            assert manager.token_file.exists()

            # Verify content
            with open(manager.token_file) as f:
                saved = json.load(f)

            assert saved["access_token"] == "test-access-token"
            assert "saved_at" in saved

    @patch.dict("os.environ", {
        "OUTCLAW_CLIENT_ID": "test-id",
        "OUTCLAW_CLIENT_SECRET": "test-secret",
    })
    @patch("outclaw.auth.ConfidentialClientApplication")
    @patch("outclaw.auth.KEYRING_AVAILABLE", False)
    def test_get_tokens_from_file(self, mock_app, tmp_path):
        """Test retrieving tokens from file."""
        from outclaw.auth import TokenManager

        # Create token file
        token_file = tmp_path / "tokens.json"
        tokens = {
            "access_token": "test-token",
            "refresh_token": "refresh-token",
            "expires_in": 3600,
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(token_file, "w") as f:
            json.dump(tokens, f)

        with patch.object(TokenManager, "token_dir", tmp_path):
            manager = TokenManager()
            manager.token_file = token_file

            result = manager.get_tokens()

            assert result["access_token"] == "test-token"

    @patch.dict("os.environ", {
        "OUTCLAW_CLIENT_ID": "test-id",
        "OUTCLAW_CLIENT_SECRET": "test-secret",
    })
    @patch("outclaw.auth.ConfidentialClientApplication")
    def test_get_access_token_no_tokens(self, mock_app):
        """Test getting access token when not authenticated."""
        from outclaw.auth import TokenManager

        manager = TokenManager()
        manager._cached_tokens = None

        with patch.object(manager, "get_tokens", return_value=None):
            with pytest.raises(AuthenticationError) as exc_info:
                manager.get_access_token()

            assert "No authentication tokens" in str(exc_info.value)

    @patch.dict("os.environ", {
        "OUTCLAW_CLIENT_ID": "test-id",
        "OUTCLAW_CLIENT_SECRET": "test-secret",
    })
    @patch("outclaw.auth.ConfidentialClientApplication")
    def test_needs_refresh_no_expiry_info(self, mock_app):
        """Test needs_refresh returns True when no expiry info."""
        from outclaw.auth import TokenManager

        manager = TokenManager()

        tokens = {"access_token": "token"}
        assert manager._needs_refresh(tokens) is True

    @patch.dict("os.environ", {
        "OUTCLAW_CLIENT_ID": "test-id",
        "OUTCLAW_CLIENT_SECRET": "test-secret",
    })
    @patch("outclaw.auth.ConfidentialClientApplication")
    def test_needs_refresh_expired(self, mock_app):
        """Test needs_refresh returns True for expired tokens."""
        from outclaw.auth import TokenManager

        manager = TokenManager()

        # Token that expired an hour ago
        saved_at = datetime.now(timezone.utc) - timedelta(hours=2)
        tokens = {
            "access_token": "token",
            "expires_in": 3600,
            "saved_at": saved_at.isoformat(),
        }

        assert manager._needs_refresh(tokens) is True

    @patch.dict("os.environ", {
        "OUTCLAW_CLIENT_ID": "test-id",
        "OUTCLAW_CLIENT_SECRET": "test-secret",
    })
    @patch("outclaw.auth.ConfidentialClientApplication")
    def test_needs_refresh_valid(self, mock_app):
        """Test needs_refresh returns False for valid tokens."""
        from outclaw.auth import TokenManager

        manager = TokenManager()

        # Token valid for another hour
        saved_at = datetime.now(timezone.utc)
        tokens = {
            "access_token": "token",
            "expires_in": 3600,
            "saved_at": saved_at.isoformat(),
        }

        assert manager._needs_refresh(tokens) is False

    @patch.dict("os.environ", {
        "OUTCLAW_CLIENT_ID": "test-id",
        "OUTCLAW_CLIENT_SECRET": "test-secret",
    })
    @patch("outclaw.auth.ConfidentialClientApplication")
    def test_clear_tokens(self, mock_app, tmp_path):
        """Test clearing tokens."""
        from outclaw.auth import TokenManager

        # Create token file
        token_file = tmp_path / "tokens.json"
        token_file.write_text('{"access_token": "test"}')

        with patch.object(TokenManager, "token_dir", tmp_path):
            manager = TokenManager()
            manager.token_file = token_file
            manager._cached_tokens = {"test": "data"}

            manager.clear_tokens()

            assert not token_file.exists()
            assert manager._cached_tokens is None

    @patch.dict("os.environ", {
        "OUTCLAW_CLIENT_ID": "test-id",
        "OUTCLAW_CLIENT_SECRET": "test-secret",
    })
    @patch("outclaw.auth.ConfidentialClientApplication")
    def test_is_authenticated_true(self, mock_app):
        """Test is_authenticated returns True when tokens exist."""
        from outclaw.auth import TokenManager

        manager = TokenManager()

        with patch.object(manager, "get_tokens", return_value={"access_token": "token"}):
            assert manager.is_authenticated is True

    @patch.dict("os.environ", {
        "OUTCLAW_CLIENT_ID": "test-id",
        "OUTCLAW_CLIENT_SECRET": "test-secret",
    })
    @patch("outclaw.auth.ConfidentialClientApplication")
    def test_is_authenticated_false(self, mock_app):
        """Test is_authenticated returns False when no tokens."""
        from outclaw.auth import TokenManager

        manager = TokenManager()

        with patch.object(manager, "get_tokens", return_value=None):
            assert manager.is_authenticated is False

    @patch.dict("os.environ", {
        "OUTCLAW_CLIENT_ID": "test-id",
        "OUTCLAW_CLIENT_SECRET": "test-secret",
    })
    @patch("outclaw.auth.ConfidentialClientApplication")
    def test_get_token_info(self, mock_app):
        """Test getting token info for status display."""
        from outclaw.auth import TokenManager

        manager = TokenManager()

        saved_at = datetime.now(timezone.utc)
        tokens = {
            "access_token": "token",
            "expires_in": 3600,
            "saved_at": saved_at.isoformat(),
            "scope": "Mail.Read Calendars.Read",
        }

        with patch.object(manager, "get_tokens", return_value=tokens):
            info = manager.get_token_info()

            assert info is not None
            assert "expires_at" in info
            assert "is_expired" in info
            assert info["is_expired"] is False
            assert "scopes" in info
            assert "Mail.Read" in info["scopes"]
