"""
Tests for the Outclaw mail module.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestMailClient:
    """Test MailClient operations."""

    @patch("officeclaw.mail.GraphClient")
    def test_list_messages(self, mock_client_class, sample_messages):
        """Test listing messages."""
        from officeclaw.mail import MailClient

        mock_client = MagicMock()
        mock_client.get_all.return_value = sample_messages
        mock_client_class.return_value = mock_client

        client = MailClient()
        messages = client.list_messages(limit=10)

        assert len(messages) == 3
        mock_client.get_all.assert_called_once()
        call_args = mock_client.get_all.call_args
        assert "/me/mailFolders/inbox/messages" in call_args[0][0]

    @patch("officeclaw.mail.GraphClient")
    def test_list_messages_with_filter(self, mock_client_class, sample_messages):
        """Test listing messages with filter."""
        from officeclaw.mail import MailClient

        mock_client = MagicMock()
        mock_client.get_all.return_value = [sample_messages[0]]
        mock_client_class.return_value = mock_client

        client = MailClient()
        messages = client.list_messages(filter_query="isRead eq false")

        assert len(messages) == 1
        call_args = mock_client.get_all.call_args
        assert "$filter" in call_args[1]["params"]

    @patch("officeclaw.mail.GraphClient")
    def test_get_message(self, mock_client_class, sample_message):
        """Test getting a specific message."""
        from officeclaw.mail import MailClient

        mock_client = MagicMock()
        mock_client.get.return_value = sample_message
        mock_client_class.return_value = mock_client

        client = MailClient()
        message = client.get_message("msg-123")

        assert message["subject"] == sample_message["subject"]
        mock_client.get.assert_called_with("/me/messages/msg-123")

    @patch("officeclaw.mail.GraphClient")
    def test_send_message(self, mock_client_class):
        """Test sending a message."""
        from officeclaw.mail import MailClient

        mock_client = MagicMock()
        mock_client.post.return_value = None
        mock_client_class.return_value = mock_client

        client = MailClient()
        client.send_message(
            to="recipient@example.com",
            subject="Test Subject",
            body="Test body",
        )

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/me/sendMail"
        assert "message" in call_args[0][1]

    @patch("officeclaw.mail.GraphClient")
    def test_send_message_multiple_recipients(self, mock_client_class):
        """Test sending to multiple recipients."""
        from officeclaw.mail import MailClient

        mock_client = MagicMock()
        mock_client.post.return_value = None
        mock_client_class.return_value = mock_client

        client = MailClient()
        client.send_message(
            to=["user1@example.com", "user2@example.com"],
            subject="Test",
            body="Body",
            cc="cc@example.com",
        )

        call_args = mock_client.post.call_args
        message = call_args[0][1]["message"]
        assert len(message["toRecipients"]) == 2
        assert len(message["ccRecipients"]) == 1

    @patch("officeclaw.mail.GraphClient")
    def test_mark_read(self, mock_client_class, sample_message):
        """Test marking message as read."""
        from officeclaw.mail import MailClient

        mock_client = MagicMock()
        updated = {**sample_message, "isRead": True}
        mock_client.patch.return_value = updated
        mock_client_class.return_value = mock_client

        client = MailClient()
        result = client.mark_read("msg-123", is_read=True)

        assert result["isRead"] is True
        mock_client.patch.assert_called_with(
            "/me/messages/msg-123",
            {"isRead": True},
        )

    @patch("officeclaw.mail.GraphClient")
    def test_delete_message(self, mock_client_class):
        """Test deleting a message."""
        from officeclaw.mail import MailClient

        mock_client = MagicMock()
        mock_client.delete.return_value = None
        mock_client_class.return_value = mock_client

        client = MailClient()
        client.delete("msg-123")

        mock_client.delete.assert_called_with("/me/messages/msg-123")

    @patch("officeclaw.mail.GraphClient")
    def test_reply(self, mock_client_class):
        """Test replying to a message."""
        from officeclaw.mail import MailClient

        mock_client = MagicMock()
        mock_client.post.return_value = None
        mock_client_class.return_value = mock_client

        client = MailClient()
        client.reply("msg-123", "Thanks for your email!")

        mock_client.post.assert_called_with(
            "/me/messages/msg-123/reply",
            {"comment": "Thanks for your email!"},
        )

    @patch("officeclaw.mail.GraphClient")
    def test_archive(self, mock_client_class, sample_message):
        """Test archiving a message."""
        from officeclaw.mail import MailClient

        mock_client = MagicMock()
        mock_client.post.return_value = sample_message
        mock_client_class.return_value = mock_client

        client = MailClient()
        client.archive("msg-123")

        mock_client.post.assert_called_with(
            "/me/messages/msg-123/move",
            {"destinationId": "archive"},
        )
