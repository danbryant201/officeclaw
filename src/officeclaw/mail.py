"""
Mail operations for Outclaw.

Provides email management through Microsoft Graph API.
"""

from __future__ import annotations

from typing import Any

from officeclaw.client import GraphClient


class MailClient:
    """
    Client for Microsoft Graph Mail API.

    Example:
        client = MailClient()
        messages = client.list_messages(limit=10)
        client.send_message("user@example.com", "Subject", "Body")
    """

    def __init__(self, graph_client: GraphClient | None = None) -> None:
        """Initialize mail client."""
        self._client = graph_client or GraphClient()
        self._owns_client = graph_client is None

    def list_messages(
        self,
        folder: str = "inbox",
        limit: int = 10,
        filter_query: str | None = None,
        search: str | None = None,
        order_by: str = "receivedDateTime desc",
        select: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        List email messages.

        Args:
            folder: Mail folder (inbox, sentItems, drafts, etc.)
            limit: Maximum messages to return
            filter_query: OData filter expression
            search: Search query
            order_by: Sort order
            select: Fields to return

        Returns:
            List of message objects
        """
        params: dict[str, Any] = {
            "$top": limit,
            "$orderby": order_by,
        }

        if select:
            params["$select"] = select
        else:
            params["$select"] = (
                "id,subject,from,toRecipients,receivedDateTime,isRead,importance,hasAttachments,bodyPreview"
            )

        if filter_query:
            params["$filter"] = filter_query

        if search:
            params["$search"] = f'"{search}"'

        endpoint = f"/me/mailFolders/{folder}/messages"
        return self._client.get_all(endpoint, params=params, limit=limit)

    def get_message(self, message_id: str) -> dict[str, Any]:
        """
        Get a specific message.

        Args:
            message_id: Message ID

        Returns:
            Message object with full details
        """
        return self._client.get(f"/me/messages/{message_id}")

    def send_message(
        self,
        to: str | list[str],
        subject: str,
        body: str,
        cc: str | list[str] | None = None,
        bcc: str | list[str] | None = None,
        content_type: str = "Text",
        save_to_sent: bool = True,
        attachments: list[dict[str, Any]] | None = None,
    ) -> None:
        """
        Send an email message.

        Args:
            to: Recipient email(s)
            subject: Email subject
            body: Email body
            cc: CC recipient(s)
            bcc: BCC recipient(s)
            content_type: "Text" or "HTML"
            save_to_sent: Save copy to Sent Items
            attachments: List of attachment dicts with @odata.type, name,
                contentType, and contentBytes (base64-encoded)
        """
        # Normalize recipients to lists
        to_list = [to] if isinstance(to, str) else to
        cc_list = [cc] if isinstance(cc, str) else (cc or [])
        bcc_list = [bcc] if isinstance(bcc, str) else (bcc or [])

        message = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": content_type,
                    "content": body,
                },
                "toRecipients": [{"emailAddress": {"address": addr}} for addr in to_list],
            },
            "saveToSentItems": save_to_sent,
        }

        if cc_list:
            message["message"]["ccRecipients"] = [
                {"emailAddress": {"address": addr}} for addr in cc_list
            ]

        if bcc_list:
            message["message"]["bccRecipients"] = [
                {"emailAddress": {"address": addr}} for addr in bcc_list
            ]

        if attachments:
            message["message"]["attachments"] = attachments

        self._client.post("/me/sendMail", message)

    def reply(
        self,
        message_id: str,
        body: str,
        reply_all: bool = False,
    ) -> None:
        """
        Reply to a message.

        Args:
            message_id: Original message ID
            body: Reply body
            reply_all: Reply to all recipients
        """
        endpoint = f"/me/messages/{message_id}/{'replyAll' if reply_all else 'reply'}"
        self._client.post(endpoint, {"comment": body})

    def forward(
        self,
        message_id: str,
        to: str | list[str],
        comment: str = "",
    ) -> None:
        """
        Forward a message.

        Args:
            message_id: Message ID to forward
            to: Recipient email(s)
            comment: Optional comment
        """
        to_list = [to] if isinstance(to, str) else to
        data = {
            "comment": comment,
            "toRecipients": [{"emailAddress": {"address": addr}} for addr in to_list],
        }
        self._client.post(f"/me/messages/{message_id}/forward", data)

    def move(self, message_id: str, folder: str) -> dict[str, Any]:
        """
        Move message to a folder.

        Args:
            message_id: Message ID
            folder: Destination folder name or ID

        Returns:
            Updated message object
        """
        # Get folder ID if name provided
        folder_id = self._get_folder_id(folder)
        return self._client.post(
            f"/me/messages/{message_id}/move",
            {"destinationId": folder_id},
        )

    def delete(self, message_id: str) -> None:
        """Delete a message."""
        self._client.delete(f"/me/messages/{message_id}")

    def mark_read(self, message_id: str, is_read: bool = True) -> dict[str, Any]:
        """
        Mark message as read or unread.

        Args:
            message_id: Message ID
            is_read: True for read, False for unread

        Returns:
            Updated message object
        """
        return self._client.patch(
            f"/me/messages/{message_id}",
            {"isRead": is_read},
        )

    def archive(self, message_id: str) -> dict[str, Any]:
        """
        Move message to Archive folder.

        Args:
            message_id: Message ID

        Returns:
            Updated message object
        """
        return self.move(message_id, "archive")

    def search(
        self,
        query: str,
        folder: str | None = None,
        limit: int = 25,
    ) -> list[dict[str, Any]]:
        """
        Search for messages.

        Args:
            query: Search query string
            folder: Specific folder to search (None = all folders)
            limit: Maximum results

        Returns:
            List of matching messages
        """
        params: dict[str, Any] = {
            "$search": f'"{query}"',
            "$top": limit,
            "$select": (
                "id,subject,from,toRecipients,receivedDateTime,isRead,importance,bodyPreview"
            ),
        }

        if folder:
            folder_id = self._get_folder_id(folder)
            endpoint = f"/me/mailFolders/{folder_id}/messages"
        else:
            endpoint = "/me/messages"

        return self._client.get_all(endpoint, params=params, limit=limit)

    def _get_folder_id(self, folder: str) -> str:
        """Get folder ID from name or return as-is if already an ID."""
        # Well-known folder names
        well_known = {
            "inbox": "inbox",
            "drafts": "drafts",
            "sentitems": "sentItems",
            "sent": "sentItems",
            "deleteditems": "deletedItems",
            "deleted": "deletedItems",
            "trash": "deletedItems",
            "archive": "archive",
            "junkemail": "junkemail",
            "junk": "junkemail",
            "spam": "junkemail",
        }

        folder_lower = folder.lower()
        if folder_lower in well_known:
            return well_known[folder_lower]

        # Assume it's already an ID
        return folder

    def list_folders(self) -> list[dict[str, Any]]:
        """List all mail folders."""
        return self._client.get_all("/me/mailFolders")

    def close(self) -> None:
        """Close the client."""
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> MailClient:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()
