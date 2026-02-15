"""
Outclaw exceptions.

Custom exception classes for handling Microsoft Graph API errors
and authentication failures.
"""

from __future__ import annotations


class OutclawError(Exception):
    """Base exception for Outclaw errors."""

    pass


class AuthenticationError(OutclawError):
    """
    Raised when authentication fails.

    This can occur when:
    - No tokens are available (user not logged in)
    - Access token is expired and refresh fails
    - Token refresh returns an error
    - Credentials are invalid

    Resolution: Run `officeclaw auth login` to re-authenticate.
    """

    pass


class GraphAPIError(OutclawError):
    """
    Raised when Microsoft Graph API returns an error.

    Attributes:
        code: Error code from Graph API (e.g., "InvalidAuthenticationToken")
        message: Human-readable error message
        status_code: HTTP status code (if available)

    Common error codes:
        - InvalidAuthenticationToken: Token expired or invalid
        - ResourceNotFound: Requested resource doesn't exist
        - AccessDenied: Insufficient permissions
        - BadRequest: Invalid request parameters
        - TooManyRequests: Rate limit exceeded
    """

    def __init__(self, code: str, message: str, status_code: int | None = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(f"{code}: {message}")


class RateLimitError(GraphAPIError):
    """
    Raised when rate limit is exceeded.

    Microsoft Graph API has rate limits (~120 requests/minute for most endpoints).
    When exceeded, wait and retry.

    Attributes:
        retry_after: Seconds to wait before retrying (if provided by API)
    """

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int | None = None):
        self.retry_after = retry_after
        super().__init__("TooManyRequests", message, 429)


class ConfigurationError(OutclawError):
    """
    Raised when configuration is missing or invalid.

    This can occur when:
    - Required environment variables are not set
    - .env file is malformed
    - Client ID or secret is invalid

    Resolution: Check .env file and environment variables.
    """

    pass


class TokenStorageError(OutclawError):
    """
    Raised when token storage operations fail.

    This can occur when:
    - Keyring is not available and file storage fails
    - File permissions prevent reading/writing tokens
    - Token file is corrupted

    Resolution: Check ~/.officeclaw/ directory permissions.
    """

    pass
