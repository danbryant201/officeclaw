"""
Tests for the Outclaw auth module.
"""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from outclaw.exceptions import AuthenticationError, ConfigurationError


class TestTokenManagerPublicClient:
    """Test TokenManager in public client (device code) mode."""

    @patch("outclaw.auth.load_dotenv")
    @patch("outclaw.auth.PublicClientApplication")
    @patch("outclaw.auth._load_msal_cache")
    @patch.dict("os.environ", {"OUTCLAW_CLIENT_ID": "test-client-id"}, clear=True)
    def test_init_public_client(self, mock_cache, mock_app, mock_dotenv):
        """Test initialization in public client mode (no secret)."""
        from outclaw.auth import TokenManager

        mock_cache.return_value = MagicMock()

        manager = TokenManager()

        assert manager.client_id == "test-client-id"
        assert manager.public_client_mode is True
        mock_app.assert_called_once()

    @patch("outclaw.auth.load_dotenv")
    @patch.dict("os.environ", {}, clear=True)
    def test_init_missing_client_id(self, mock_dotenv):
        """Test initialization fails without client ID."""
        from outclaw.auth import TokenManager

        with pytest.raises(ConfigurationError) as exc_info:
            TokenManager()

        assert "OUTCLAW_CLIENT_ID" in str(exc_info.value)

    @patch("outclaw.auth.load_dotenv")
    @patch("outclaw.auth.PublicClientApplication")
    @patch("outclaw.auth._load_msal_cache")
    @patch.dict("os.environ", {"OUTCLAW_CLIENT_ID": "test-id"}, clear=True)
    def test_get_access_token_no_accounts(self, mock_cache, mock_app_class, mock_dotenv):
        """Test getting access token when not authenticated."""
        from outclaw.auth import TokenManager

        mock_cache.return_value = MagicMock()
        mock_app = MagicMock()
        mock_app.get_accounts.return_value = []
        mock_app_class.return_value = mock_app

        manager = TokenManager()

        with pytest.raises(AuthenticationError) as exc_info:
            manager.get_access_token()

        assert "No authentication tokens" in str(exc_info.value)

    @patch("outclaw.auth.load_dotenv")
    @patch("outclaw.auth._save_msal_cache")
    @patch("outclaw.auth.PublicClientApplication")
    @patch("outclaw.auth._load_msal_cache")
    @patch.dict("os.environ", {"OUTCLAW_CLIENT_ID": "test-id"}, clear=True)
    def test_get_access_token_success(self, mock_cache, mock_app_class, mock_save, mock_dotenv):
        """Test successful token acquisition via silent flow."""
        from outclaw.auth import TokenManager

        mock_cache.return_value = MagicMock()
        mock_app = MagicMock()
        mock_app.get_accounts.return_value = [{"username": "user@outlook.com"}]
        mock_app.acquire_token_silent.return_value = {
            "access_token": "test-access-token",
            "expires_in": 3600,
        }
        mock_app_class.return_value = mock_app

        manager = TokenManager()
        token = manager.get_access_token()

        assert token == "test-access-token"
        mock_app.acquire_token_silent.assert_called_once()

    @patch("outclaw.auth.load_dotenv")
    @patch("outclaw.auth.PublicClientApplication")
    @patch("outclaw.auth._load_msal_cache")
    @patch.dict("os.environ", {"OUTCLAW_CLIENT_ID": "test-id"}, clear=True)
    def test_get_access_token_silent_fails(self, mock_cache, mock_app_class, mock_dotenv):
        """Test error when silent acquisition fails."""
        from outclaw.auth import TokenManager

        mock_cache.return_value = MagicMock()
        mock_app = MagicMock()
        mock_app.get_accounts.return_value = [{"username": "user@outlook.com"}]
        mock_app.acquire_token_silent.return_value = None
        mock_app_class.return_value = mock_app

        manager = TokenManager()

        with pytest.raises(AuthenticationError) as exc_info:
            manager.get_access_token()

        assert "outclaw auth login" in str(exc_info.value)

    @patch("outclaw.auth.load_dotenv")
    @patch("outclaw.auth.PublicClientApplication")
    @patch("outclaw.auth._load_msal_cache")
    @patch.dict("os.environ", {"OUTCLAW_CLIENT_ID": "test-id"}, clear=True)
    def test_is_authenticated_true(self, mock_cache, mock_app_class, mock_dotenv):
        """Test is_authenticated returns True when accounts exist."""
        from outclaw.auth import TokenManager

        mock_cache.return_value = MagicMock()
        mock_app = MagicMock()
        mock_app.get_accounts.return_value = [{"username": "user@outlook.com"}]
        mock_app_class.return_value = mock_app

        manager = TokenManager()
        assert manager.is_authenticated is True

    @patch("outclaw.auth.load_dotenv")
    @patch("outclaw.auth.PublicClientApplication")
    @patch("outclaw.auth._load_msal_cache")
    @patch.dict("os.environ", {"OUTCLAW_CLIENT_ID": "test-id"}, clear=True)
    def test_is_authenticated_false(self, mock_cache, mock_app_class, mock_dotenv):
        """Test is_authenticated returns False when no accounts."""
        from outclaw.auth import TokenManager

        mock_cache.return_value = MagicMock()
        mock_app = MagicMock()
        mock_app.get_accounts.return_value = []
        mock_app_class.return_value = mock_app

        manager = TokenManager()
        assert manager.is_authenticated is False

    @patch("outclaw.auth.load_dotenv")
    @patch("outclaw.auth.CACHE_FILE")
    @patch("outclaw.auth.PublicClientApplication")
    @patch("outclaw.auth._load_msal_cache")
    @patch.dict("os.environ", {"OUTCLAW_CLIENT_ID": "test-id"}, clear=True)
    def test_clear_tokens(self, mock_cache, mock_app_class, mock_cache_file, mock_dotenv):
        """Test clearing tokens in public client mode."""
        from outclaw.auth import TokenManager

        mock_cache.return_value = MagicMock()
        mock_app_class.return_value = MagicMock()
        mock_cache_file.exists.return_value = True

        manager = TokenManager()
        manager.clear_tokens()

        mock_cache_file.unlink.assert_called_once()


class TestTokenManagerConfidentialClient:
    """Test TokenManager in confidential client (legacy) mode."""

    @patch.dict("os.environ", {
        "OUTCLAW_CLIENT_ID": "test-client-id",
        "OUTCLAW_CLIENT_SECRET": "test-client-secret",
    })
    @patch("outclaw.auth.ConfidentialClientApplication")
    def test_init_confidential_client(self, mock_app):
        """Test initialization in confidential client mode."""
        from outclaw.auth import TokenManager

        manager = TokenManager()

        assert manager.client_id == "test-client-id"
        assert manager.client_secret == "test-client-secret"
        assert manager.public_client_mode is False

    @patch.dict("os.environ", {
        "OUTCLAW_CLIENT_ID": "test-id",
        "OUTCLAW_CLIENT_SECRET": "test-secret",
    })
    @patch("outclaw.auth.ConfidentialClientApplication")
    @patch("outclaw.auth.KEYRING_AVAILABLE", False)
    def test_save_tokens_to_file(self, mock_app, tmp_path):
        """Test saving tokens to file when keyring unavailable."""
        from outclaw.auth import TokenManager

        manager = TokenManager()
        manager.token_dir = tmp_path
        manager.token_file = tmp_path / "tokens.json"

        tokens = {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "expires_in": 3600,
        }

        manager.save_tokens(tokens)

        assert manager.token_file.exists()

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

        token_file = tmp_path / "tokens.json"
        tokens = {
            "access_token": "test-token",
            "refresh_token": "refresh-token",
            "expires_in": 3600,
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(token_file, "w") as f:
            json.dump(tokens, f)

        manager = TokenManager()
        manager.token_file = token_file
        manager._cached_tokens = None

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

        token_file = tmp_path / "tokens.json"
        token_file.write_text('{"access_token": "test"}')

        manager = TokenManager()
        manager.token_dir = tmp_path
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
            assert info["mode"] == "confidential_client (authorization code flow)"
