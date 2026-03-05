"""
Google Calendar Sync

Syncs TimeTree events to Google Calendar using the Google Calendar API.
"""

import os
import pickle
import hashlib
import json
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

    def delete_events_by_titles(self, calendar_id: str, titles: List[str]) -> int:
        """Delete Google Calendar events whose summaries match any of the given titles."""
        titles_set = set(titles)
        deleted = 0
        page_token = None
        while True:
            result = self.service.events().list(
                calendarId=calendar_id,
                maxResults=2500,
                pageToken=page_token
            ).execute()
            for event in result.get('items', []):
                if event.get('summary') in titles_set:
                    self.service.events().delete(
                        calendarId=calendar_id,
                        eventId=event['id']
                    ).execute()
                    print(f"  Deleted: {event.get('summary')}")
                    deleted += 1
            page_token = result.get('nextPageToken')
            if not page_token:
                break
        return deleted

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
        stats = {'created': 0, 'updated': 0, 'skipped': 0, 'deleted': 0, 'failed': 0, 'cleared': 0}

        if clear_existing:
            print("Clearing existing events...")
            stats['cleared'] = self._clear_calendar(calendar_id)
            print(f"Syncing {len(events)} events...")
            for event in events:
                result = self.create_event(calendar_id, event, timezone)
                if result:
                    stats['created'] += 1
                else:
                    stats['failed'] += 1
            return stats

        # Smart sync: compare against what's already in Google Calendar
        print("Fetching existing synced events...")
        existing = self._get_synced_events(calendar_id)

        timetree_ids = set()
        print(f"Syncing {len(events)} events...")
        for event in events:
            timetree_id = str(event.get('id', ''))
            if not timetree_id:
                continue
            timetree_ids.add(timetree_id)
            new_hash = self._compute_hash(event)

            if timetree_id not in existing:
                result = self.create_event(calendar_id, event, timezone)
                if result:
                    stats['created'] += 1
                    print(f"  + Created: {event.get('title', 'Untitled')}")
                else:
                    stats['failed'] += 1
                    print(f"  ✗ Failed: {event.get('title', 'Untitled')}")
            elif existing[timetree_id]['hash'] != new_hash:
                result = self._update_event(calendar_id, existing[timetree_id]['google_id'], event, timezone)
                if result:
                    stats['updated'] += 1
                    print(f"  ~ Updated: {event.get('title', 'Untitled')}")
                else:
                    stats['failed'] += 1
                    print(f"  ✗ Failed: {event.get('title', 'Untitled')}")
            else:
                stats['skipped'] += 1

        # Delete Google Calendar events that no longer exist in TimeTree
        for timetree_id, info in existing.items():
            if timetree_id not in timetree_ids:
                try:
                    self.service.events().delete(
                        calendarId=calendar_id,
                        eventId=info['google_id']
                    ).execute()
                    stats['deleted'] += 1
                    print(f"  - Deleted: {info.get('title', 'removed event')}")
                except HttpError:
                    stats['failed'] += 1

        return stats

    def _get_synced_events(self, calendar_id: str) -> Dict[str, Dict]:
        """Fetch all Google Calendar events previously synced from TimeTree."""
        result = {}
        page_token = None
        while True:
            response = self.service.events().list(
                calendarId=calendar_id,
                privateExtendedProperty='timetree_synced=true',
                maxResults=2500,
                pageToken=page_token
            ).execute()
            for event in response.get('items', []):
                private = event.get('extendedProperties', {}).get('private', {})
                timetree_id = private.get('timetree_id')
                if timetree_id:
                    result[timetree_id] = {
                        'google_id': event['id'],
                        'hash': private.get('timetree_hash', ''),
                        'title': event.get('summary', ''),
                    }
            page_token = response.get('nextPageToken')
            if not page_token:
                break
        return result

    def _update_event(self, calendar_id: str, google_event_id: str, event_data: Dict, timezone: str = 'UTC') -> Optional[Dict]:
        """Update an existing Google Calendar event."""
        google_event = self._convert_to_google_event(event_data, timezone)
        try:
            return self.service.events().update(
                calendarId=calendar_id,
                eventId=google_event_id,
                body=google_event
            ).execute()
        except HttpError as error:
            print(f"An error occurred updating event: {error}")
            return None

    @staticmethod
    def _compute_hash(event_data: Dict) -> str:
        """Compute a hash of the event fields we care about for change detection."""
        key_fields = {
            'title': event_data.get('title'),
            'start_at': event_data.get('start_at'),
            'end_at': event_data.get('end_at'),
            'note': event_data.get('note'),
            'location_name': event_data.get('location_name'),
        }
        return hashlib.md5(json.dumps(key_fields, sort_keys=True).encode()).hexdigest()

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
            'extendedProperties': {
                'private': {
                    'timetree_synced': 'true',
                    'timetree_id': str(event_data.get('id', '')),
                    'timetree_hash': GoogleCalendarSync._compute_hash(event_data),
                }
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
