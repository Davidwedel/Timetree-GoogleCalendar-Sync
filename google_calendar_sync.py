"""
Google Calendar Sync

Syncs TimeTree events to Google Calendar using the Google Calendar API.
"""

import os
import pickle
from datetime import datetime
from typing import List, Dict, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pytz


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']


class GoogleCalendarSync:
    """Syncs events to Google Calendar."""

    def __init__(self, credentials_file: str = 'credentials.json', token_file: str = 'token.json'):
        """
        Initialize Google Calendar sync.

        Args:
            credentials_file: Path to OAuth 2.0 credentials file from Google Cloud Console
            token_file: Path to store the user's access and refresh tokens
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.creds = None
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Calendar API."""
        # Load existing credentials if available
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                self.creds = pickle.load(token)

        # If credentials don't exist or are invalid, get new ones
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Credentials file '{self.credentials_file}' not found. "
                        "Please download it from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                self.creds = flow.run_local_server(port=0)

            # Save credentials for next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(self.creds, token)

        # Build the service
        self.service = build('calendar', 'v3', credentials=self.creds)

    def get_calendars(self) -> List[Dict]:
        """
        Get list of all calendars.

        Returns:
            List of calendar dictionaries
        """
        try:
            calendar_list = self.service.calendarList().list().execute()
            return calendar_list.get('items', [])
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def create_event(
        self,
        calendar_id: str,
        event_data: Dict,
        timezone: str = 'UTC'
    ) -> Optional[Dict]:
        """
        Create a single event in Google Calendar.

        Args:
            calendar_id: Google Calendar ID (usually email or 'primary')
            event_data: TimeTree event dictionary
            timezone: Timezone for the event

        Returns:
            Created event dictionary or None if failed
        """
        # Convert TimeTree event to Google Calendar event format
        google_event = self._convert_to_google_event(event_data, timezone)

        try:
            created_event = self.service.events().insert(
                calendarId=calendar_id,
                body=google_event
            ).execute()
            return created_event
        except HttpError as error:
            print(f"An error occurred creating event: {error}")
            return None

    def sync_events(
        self,
        calendar_id: str,
        events: List[Dict],
        timezone: str = 'UTC',
        clear_existing: bool = False
    ) -> Dict[str, int]:
        """
        Sync multiple events to Google Calendar.

        Args:
            calendar_id: Google Calendar ID
            events: List of TimeTree event dictionaries
            timezone: Timezone for events
            clear_existing: If True, clear existing events before syncing

        Returns:
            Dictionary with sync statistics
        """
        stats = {'created': 0, 'failed': 0, 'cleared': 0}

        # Optionally clear existing events
        if clear_existing:
            print("Clearing existing events...")
            stats['cleared'] = self._clear_calendar(calendar_id)

        # Create events
        print(f"Syncing {len(events)} events...")
        for event in events:
            result = self.create_event(calendar_id, event, timezone)
            if result:
                stats['created'] += 1
                print(f"  ✓ Created: {event.get('title', 'Untitled')}")
            else:
                stats['failed'] += 1
                print(f"  ✗ Failed: {event.get('title', 'Untitled')}")

        return stats

    def _clear_calendar(self, calendar_id: str) -> int:
        """
        Clear all events from a calendar.

        Args:
            calendar_id: Google Calendar ID

        Returns:
            Number of events deleted
        """
        deleted_count = 0
        try:
            # Get all events
            events_result = self.service.events().list(
                calendarId=calendar_id,
                maxResults=2500
            ).execute()
            events = events_result.get('items', [])

            # Delete each event
            for event in events:
                self.service.events().delete(
                    calendarId=calendar_id,
                    eventId=event['id']
                ).execute()
                deleted_count += 1

        except HttpError as error:
            print(f"An error occurred clearing calendar: {error}")

        return deleted_count

    @staticmethod
    def _parse_datetime(dt_string: str) -> datetime:
        """Parse TimeTree datetime string."""
        try:
            timestamp_ms = int(dt_string)
            return datetime.fromtimestamp(timestamp_ms / 1000, tz=pytz.UTC)
        except (ValueError, TypeError):
            pass

        try:
            if 'Z' in dt_string or '+' in dt_string:
                return datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
            else:
                return datetime.fromisoformat(dt_string).replace(tzinfo=pytz.UTC)
        except (ValueError, TypeError):
            return datetime.now(tz=pytz.UTC)

    def _convert_to_google_event(self, event_data: Dict, timezone: str = 'UTC') -> Dict:
        """
        Convert TimeTree event to Google Calendar event format.

        Args:
            event_data: TimeTree event dictionary
            timezone: Timezone for the event

        Returns:
            Google Calendar event dictionary
        """
        start_dt = self._parse_datetime(event_data.get('start_at', ''))
        end_dt = self._parse_datetime(event_data.get('end_at', ''))

        google_event = {
            'summary': event_data.get('title', 'Untitled Event'),
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': timezone,
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': timezone,
            },
        }

        # Optional fields
        if event_data.get('note'):
            google_event['description'] = event_data['note']

        if event_data.get('location_name'):
            google_event['location'] = event_data['location_name']

        if event_data.get('url'):
            if 'description' in google_event:
                google_event['description'] += f"\n\nURL: {event_data['url']}"
            else:
                google_event['description'] = f"URL: {event_data['url']}"

        return google_event


def main():
    """Example usage."""
    from dotenv import load_dotenv
    load_dotenv()

    # Initialize sync
    sync = GoogleCalendarSync()

    # Get calendar ID from environment
    calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')

    # List calendars
    print("Available calendars:")
    calendars = sync.get_calendars()
    for cal in calendars:
        print(f"  - {cal['summary']} (ID: {cal['id']})")

    # Example event
    sample_event = {
        'id': 'test-event-1',
        'title': 'Test Sync Event',
        'start_at': '2026-03-05T10:00:00Z',
        'end_at': '2026-03-05T11:00:00Z',
        'note': 'Synced from TimeTree',
        'location_name': 'Test Location'
    }

    # Sync event
    print(f"\nSyncing to calendar: {calendar_id}")
    result = sync.create_event(calendar_id, sample_event)
    if result:
        print(f"✓ Event created: {result.get('htmlLink')}")
    else:
        print("✗ Failed to create event")


if __name__ == "__main__":
    main()
