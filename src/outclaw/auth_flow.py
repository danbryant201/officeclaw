"""
Authentication flow for Outclaw.

Handles OAuth 2.0 Authorization Code Flow with browser-based login.
"""

from __future__ import annotations

import http.server
import os
import socketserver
import threading
import webbrowser
from typing import Any
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv
from msal import ConfidentialClientApplication
from rich.console import Console

from outclaw.auth import TokenManager
from outclaw.exceptions import AuthenticationError, ConfigurationError

console = Console()


class AuthCallbackHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler for OAuth callback."""

    auth_code: str | None = None
    error: str | None = None

    def do_GET(self) -> None:
        """Handle GET request (OAuth callback)."""
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if "code" in params:
            AuthCallbackHandler.auth_code = params["code"][0]
            self._send_success()
        elif "error" in params:
            AuthCallbackHandler.error = params.get("error_description", params["error"])[0]
            self._send_error()
        else:
            self._send_error("No authorization code received")

    def _send_success(self) -> None:
        """Send success response."""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Outclaw - Authentication Successful</title>
            <style>
                body { font-family: system-ui, sans-serif; text-align: center; padding: 50px; }
                .success { color: #22c55e; font-size: 48px; }
                h1 { color: #333; }
                p { color: #666; }
            </style>
        </head>
        <body>
            <div class="success">✓</div>
            <h1>Authentication Successful!</h1>
            <p>You can close this window and return to the terminal.</p>
        </body>
        </html>
        """
        self.wfile.write(html.encode())

    def _send_error(self, message: str = "Authentication failed") -> None:
        """Send error response."""
        self.send_response(400)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Outclaw - Authentication Failed</title>
            <style>
                body {{ font-family: system-ui, sans-serif; text-align: center; padding: 50px; }}
                .error {{ color: #ef4444; font-size: 48px; }}
                h1 {{ color: #333; }}
                p {{ color: #666; }}
            </style>
        </head>
        <body>
            <div class="error">✗</div>
            <h1>Authentication Failed</h1>
            <p>{message}</p>
        </body>
        </html>
        """
        self.wfile.write(html.encode())

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress HTTP server logging."""
        pass


def run_auth_flow() -> dict[str, Any]:
    """
    Run the OAuth 2.0 Authorization Code Flow.

    Opens browser for user authentication, handles callback,
    and stores tokens securely.

    Returns:
        Token dictionary

    Raises:
        AuthenticationError: If authentication fails
        ConfigurationError: If configuration is invalid
    """
    load_dotenv()

    # Load configuration
    client_id = os.getenv("OUTCLAW_CLIENT_ID")
    client_secret = os.getenv("OUTCLAW_CLIENT_SECRET")
    redirect_uri = os.getenv("OUTCLAW_REDIRECT_URI", "http://localhost:8000/callback")
    tenant_id = os.getenv("OUTCLAW_TENANT_ID", "consumers")
    scopes_str = os.getenv("OUTCLAW_SCOPES")

    scopes = scopes_str.split() if scopes_str else TokenManager.DEFAULT_SCOPES

    if not client_id:
        raise ConfigurationError(
            "OUTCLAW_CLIENT_ID is required. " "Set it in .env or as an environment variable."
        )

    if not client_secret:
        raise ConfigurationError(
            "OUTCLAW_CLIENT_SECRET is required. " "Set it in .env or as an environment variable."
        )

    # Parse redirect URI to get port
    parsed_uri = urlparse(redirect_uri)
    port = parsed_uri.port or 8000

    # Build authority URL
    authority = f"https://login.microsoftonline.com/{tenant_id}"

    # Initialize MSAL app
    app = ConfidentialClientApplication(
        client_id=client_id,
        client_credential=client_secret,
        authority=authority,
    )

    # Get authorization URL
    auth_url = app.get_authorization_request_url(
        scopes=scopes,
        redirect_uri=redirect_uri,
    )

    console.print("\n[bold]Outclaw Authentication[/bold]\n")
    console.print("Opening browser for Microsoft login...")
    console.print("[dim]If browser doesn't open, visit:[/dim]")
    console.print(f"[link]{auth_url}[/link]\n")

    # Reset handler state
    AuthCallbackHandler.auth_code = None
    AuthCallbackHandler.error = None

    # Start callback server
    server = socketserver.TCPServer(("", port), AuthCallbackHandler)
    server_thread = threading.Thread(target=server.handle_request)
    server_thread.start()

    # Open browser
    webbrowser.open(auth_url)

    console.print("[dim]Waiting for authentication...[/dim]")

    # Wait for callback
    server_thread.join(timeout=300)  # 5 minute timeout
    server.server_close()

    # Check result
    if AuthCallbackHandler.error:
        raise AuthenticationError(f"Authentication failed: {AuthCallbackHandler.error}")

    if not AuthCallbackHandler.auth_code:
        raise AuthenticationError("No authorization code received. Authentication timed out.")

    console.print("[dim]Exchanging code for tokens...[/dim]")

    # Exchange code for tokens
    result = app.acquire_token_by_authorization_code(
        code=AuthCallbackHandler.auth_code,
        scopes=scopes,
        redirect_uri=redirect_uri,
    )

    if "error" in result:
        error_desc = result.get("error_description", result["error"])
        raise AuthenticationError(f"Token exchange failed: {error_desc}")

    if "access_token" not in result:
        raise AuthenticationError("No access token in response")

    # Save tokens
    manager = TokenManager()
    manager.save_tokens(result)

    console.print("\n[green]✓[/green] [bold]Authentication successful![/bold]")
    console.print(f"[dim]Tokens stored in: {manager.get_token_info()['storage_location']}[/dim]\n")

    return result


if __name__ == "__main__":
    try:
        run_auth_flow()
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1) from e
