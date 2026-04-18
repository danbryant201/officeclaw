"""
Tests for the Outclaw calendar module.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestCalendarClient:
    """Test CalendarClient operations."""

    @patch("officeclaw.calendar.GraphClient")
    def test_list_events(self, mock_client_class, sample_events):
        """Test listing events."""
        from officeclaw.calendar import CalendarClient

        mock_client = MagicMock()
        mock_client.get_all.return_value = sample_events
        mock_client_class.return_value = mock_client

        client = CalendarClient()
        events = client.list_events("2026-02-01", "2026-02-28")

        assert len(events) == 3
        mock_client.get_all.assert_called_once()
        call_args = mock_client.get_all.call_args
        assert "/me/calendarView" in call_args[0][0]

    @patch("officeclaw.calendar.GraphClient")
    def test_list_events_with_dates(self, mock_client_class, sample_events):
        """Test listing events with date parameters."""
        from officeclaw.calendar import CalendarClient

        mock_client = MagicMock()
        mock_client.get_all.return_value = sample_events
        mock_client_class.return_value = mock_client

        client = CalendarClient()
        client.list_events("2026-02-01", "2026-02-28", limit=10)

        call_args = mock_client.get_all.call_args
        params = call_args[1]["params"]
        assert "startDateTime" in params
        assert "endDateTime" in params
        assert "2026-02-01" in params["startDateTime"]
        assert "2026-02-28" in params["endDateTime"]

    @patch("officeclaw.calendar.GraphClient")
    def test_get_event(self, mock_client_class, sample_event):
        """Test getting a specific event."""
        from officeclaw.calendar import CalendarClient

        mock_client = MagicMock()
        mock_client.get.return_value = sample_event
        mock_client_class.return_value = mock_client

        client = CalendarClient()
        event = client.get_event("evt-123")

        assert event["subject"] == sample_event["subject"]
        mock_client.get.assert_called_with("/me/events/evt-123")

    @patch("officeclaw.calendar.GraphClient")
    def test_create_event(self, mock_client_class, sample_event):
        """Test creating an event."""
        from officeclaw.calendar import CalendarClient

        mock_client = MagicMock()
        mock_client.post.return_value = sample_event
        mock_client_class.return_value = mock_client

        client = CalendarClient()
        event = client.create_event(
            subject="Team Meeting",
            start="2026-02-15T10:00:00",
            end="2026-02-15T11:00:00",
        )

        assert event["subject"] == sample_event["subject"]
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/me/events"
        assert call_args[0][1]["subject"] == "Team Meeting"

    @patch("officeclaw.calendar.GraphClient")
    def test_create_event_with_attendees(self, mock_client_class, sample_event):
        """Test creating event with attendees."""
        from officeclaw.calendar import CalendarClient

        mock_client = MagicMock()
        mock_client.post.return_value = sample_event
        mock_client_class.return_value = mock_client

        client = CalendarClient()
        client.create_event(
            subject="Meeting",
            start="2026-02-15T10:00:00",
            end="2026-02-15T11:00:00",
            attendees=["user1@example.com", "user2@example.com"],
        )

        call_args = mock_client.post.call_args
        event_data = call_args[0][1]
        assert "attendees" in event_data
        assert len(event_data["attendees"]) == 2

    @patch("officeclaw.calendar.GraphClient")
    def test_create_online_meeting(self, mock_client_class, sample_event):
        """Test creating Teams meeting."""
        from officeclaw.calendar import CalendarClient

        mock_client = MagicMock()
        mock_client.post.return_value = sample_event
        mock_client_class.return_value = mock_client

        client = CalendarClient()
        client.create_event(
            subject="Teams Call",
            start="2026-02-15T10:00:00",
            end="2026-02-15T11:00:00",
            is_online_meeting=True,
        )

        call_args = mock_client.post.call_args
        event_data = call_args[0][1]
        assert event_data["isOnlineMeeting"] is True

    @patch("officeclaw.calendar.GraphClient")
    def test_create_event_with_body(self, mock_client_class, sample_event):
        """Test creating event with body description."""
        from officeclaw.calendar import CalendarClient

        mock_client = MagicMock()
        mock_client.post.return_value = sample_event
        mock_client_class.return_value = mock_client

        client = CalendarClient()
        client.create_event(
            subject="Meeting",
            start="2026-02-15T10:00:00",
            end="2026-02-15T11:00:00",
            body="Agenda: Q1 review",
        )

        call_args = mock_client.post.call_args
        event_data = call_args[0][1]
        assert "body" in event_data
        assert event_data["body"]["content"] == "Agenda: Q1 review"
        assert event_data["body"]["contentType"] == "Text"

    @patch("officeclaw.calendar.GraphClient")
    def test_update_subject_does_not_wipe_body(self, mock_client_class, sample_event):
        """Updating only the subject must not include body in the PATCH payload.

        The Graph API performs a partial update — omitting a field leaves the
        existing value intact, so the body is only overwritten if explicitly sent.
        """
        from officeclaw.calendar import CalendarClient

        mock_client = MagicMock()
        created = {**sample_event, "body": {"contentType": "Text", "content": "Agenda: Q1 review"}}
        mock_client.post.return_value = created
        mock_client.patch.return_value = {**created, "subject": "Updated Meeting"}
        mock_client_class.return_value = mock_client

        client = CalendarClient()
        client.create_event(
            subject="Meeting",
            start="2026-02-15T10:00:00",
            end="2026-02-15T11:00:00",
            body="Agenda: Q1 review",
        )
        client.update_event("evt-123", subject="Updated Meeting")

        patch_data = mock_client.patch.call_args[0][1]
        assert patch_data["subject"] == "Updated Meeting"
        assert "body" not in patch_data

    @patch("officeclaw.calendar.GraphClient")
    def test_create_all_day_event(self, mock_client_class, sample_event):
        """Test creating an all-day event."""
        from officeclaw.calendar import CalendarClient

        mock_client = MagicMock()
        mock_client.post.return_value = sample_event
        mock_client_class.return_value = mock_client

        client = CalendarClient()
        client.create_event(
            subject="Holiday",
            start="2026-04-18",
            end="2026-04-19",
            is_all_day=True,
        )

        call_args = mock_client.post.call_args
        event_data = call_args[0][1]
        assert event_data["isAllDay"] is True

    @patch("officeclaw.calendar.GraphClient")
    def test_update_event_all_day(self, mock_client_class, sample_event):
        """Test updating an event to all-day."""
        from officeclaw.calendar import CalendarClient

        mock_client = MagicMock()
        mock_client.patch.return_value = sample_event
        mock_client_class.return_value = mock_client

        client = CalendarClient()
        client.update_event("evt-123", is_all_day=True)

        call_args = mock_client.patch.call_args
        patch_data = call_args[0][1]
        assert patch_data["isAllDay"] is True

    @patch("officeclaw.calendar.GraphClient")
    def test_update_event_online_meeting(self, mock_client_class, sample_event):
        """Test updating an event to add Teams meeting link."""
        from officeclaw.calendar import CalendarClient

        mock_client = MagicMock()
        mock_client.patch.return_value = sample_event
        mock_client_class.return_value = mock_client

        client = CalendarClient()
        client.update_event("evt-123", is_online_meeting=True)

        call_args = mock_client.patch.call_args
        patch_data = call_args[0][1]
        assert patch_data["isOnlineMeeting"] is True
        assert patch_data["onlineMeetingProvider"] == "teamsForBusiness"

    @patch("officeclaw.calendar.GraphClient")
    def test_update_event(self, mock_client_class, sample_event):
        """Test updating an event."""
        from officeclaw.calendar import CalendarClient

        mock_client = MagicMock()
        updated = {**sample_event, "subject": "Updated Meeting"}
        mock_client.patch.return_value = updated
        mock_client_class.return_value = mock_client

        client = CalendarClient()
        result = client.update_event("evt-123", subject="Updated Meeting")

        assert result["subject"] == "Updated Meeting"
        mock_client.patch.assert_called_once()

    @patch("officeclaw.calendar.GraphClient")
    def test_delete_event(self, mock_client_class):
        """Test deleting an event."""
        from officeclaw.calendar import CalendarClient

        mock_client = MagicMock()
        mock_client.delete.return_value = None
        mock_client_class.return_value = mock_client

        client = CalendarClient()
        client.delete_event("evt-123")

        mock_client.delete.assert_called_with("/me/events/evt-123")

    @patch("officeclaw.calendar.GraphClient")
    def test_accept_event(self, mock_client_class):
        """Test accepting meeting invitation."""
        from officeclaw.calendar import CalendarClient

        mock_client = MagicMock()
        mock_client.post.return_value = None
        mock_client_class.return_value = mock_client

        client = CalendarClient()
        client.accept_event("evt-123", comment="Looking forward to it!")

        mock_client.post.assert_called_with(
            "/me/events/evt-123/accept",
            {"comment": "Looking forward to it!", "sendResponse": True},
        )

    @patch("officeclaw.calendar.GraphClient")
    def test_decline_event(self, mock_client_class):
        """Test declining meeting invitation."""
        from officeclaw.calendar import CalendarClient

        mock_client = MagicMock()
        mock_client.post.return_value = None
        mock_client_class.return_value = mock_client

        client = CalendarClient()
        client.decline_event("evt-123", comment="Can't make it")

        mock_client.post.assert_called_with(
            "/me/events/evt-123/decline",
            {"comment": "Can't make it", "sendResponse": True},
        )

    def test_normalize_datetime_date_only(self):
        """Test datetime normalization with date only."""
        from officeclaw.calendar import CalendarClient

        client = CalendarClient.__new__(CalendarClient)

        result = client._normalize_datetime("2026-02-15")
        assert result == "2026-02-15T00:00:00"

        result = client._normalize_datetime("2026-02-15", end_of_day=True)
        assert result == "2026-02-15T23:59:59"

    def test_normalize_datetime_full(self):
        """Test datetime normalization with full datetime."""
        from officeclaw.calendar import CalendarClient

        client = CalendarClient.__new__(CalendarClient)

        result = client._normalize_datetime("2026-02-15T10:30:00")
        assert result == "2026-02-15T10:30:00"

        # Strips Z suffix
        result = client._normalize_datetime("2026-02-15T10:30:00Z")
        assert result == "2026-02-15T10:30:00"
