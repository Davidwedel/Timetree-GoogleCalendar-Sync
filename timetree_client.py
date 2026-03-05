"""
TimeTree API Client

This module provides functionality to fetch events from TimeTree calendars
using browser session cookies for authentication.
"""

import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv


class TimeTreeClient:
    """Client for interacting with TimeTree's internal API."""

    BASE_URL = "https://timetreeapp.com"

    def __init__(self, session_cookie: Optional[str] = None, csrf_token: Optional[str] = None):
        """
        Initialize the TimeTree client.

        Args:
            session_cookie: TimeTree session cookie (_session_id). If not provided, will try to load from .env
            csrf_token: CSRF token (X-CSRF-Token). If not provided, will try to load from .env
        """
        load_dotenv()
        self.session_cookie = session_cookie or os.getenv('TIMETREE_SESSION_COOKIE')
        self.csrf_token = csrf_token or os.getenv('TIMETREE_CSRF_TOKEN')

        if not self.session_cookie:
            raise ValueError(
                "TimeTree session cookie not provided. "
                "Set TIMETREE_SESSION_COOKIE in .env or pass as argument."
            )

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0',
            'X-TimeTreeA': 'web/2.1.0/en',
            'Accept': '*/*',
            'Content-Type': 'application/json',
        })

        # Set the session cookie (TimeTree uses _session_id)
        self.session.cookies.set('_session_id', self.session_cookie, domain='timetreeapp.com')

        # Set CSRF token if provided
        if self.csrf_token:
            self.session.headers['X-CSRF-Token'] = self.csrf_token

    def get_calendars(self) -> List[Dict]:
        """
        Fetch all calendars accessible to the authenticated user.

        Returns:
            List of calendar dictionaries
        """
        url = f"{self.BASE_URL}/api/v2/calendars"

        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()

            # The response structure may vary - adjust based on actual API response
            calendars = data.get('calendars', [])
            return calendars

        except requests.exceptions.RequestException as e:
            print(f"Error fetching calendars: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            raise

    def get_events(
        self,
        calendar_id: str,
        days_forward: int = 30,
        days_back: int = 7
    ) -> List[Dict]:
        """
        Fetch events from a specific calendar.

        Args:
            calendar_id: The TimeTree calendar ID
            days_forward: Number of days into the future to fetch (default: 30)
            days_back: Number of days into the past to fetch (default: 7)

        Returns:
            List of event dictionaries
        """
        now = datetime.now()
        # Go back further in the past to catch events
        start = now - timedelta(days=days_back)

        # Convert to milliseconds timestamp
        # Try using 0 to get all events
        since_ms = 0  # Get all events from beginning of time

        print(f"DEBUG: Requesting events from event_activities endpoint")

        # Use the event_activities/latest endpoint that actually returns events
        url = f"{self.BASE_URL}/api/v1/event_activities/latest"
        params = {
            'calendar_ids[]': calendar_id
        }

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            print(f"DEBUG: Response status: {response.status_code}")
            print(f"DEBUG: Response keys: {list(data.keys())}")

            # Extract events from response - try multiple possible keys
            events = data.get('events', [])

            # If no events found, check if this is a different response format
            if not events and 'data' in data:
                events = data['data'].get('events', [])

            # Filter out deactivated events
            events = [e for e in events if e.get('deactivated_at') is None]

            print(f"DEBUG: Raw API returned {len(events)} events")
            if events and len(events) > 0:
                print(f"DEBUG: First event: {events[0].get('title', 'No title')}")
                print(f"DEBUG: First event start_at: {events[0].get('start_at')}")

            # Filter to only include events within the requested date range
            end = now + timedelta(days=days_forward)
            end_ms = int(end.timestamp() * 1000)

            print(f"DEBUG: Filtering range: {since_ms} to {end_ms}")

            filtered_events = []
            for event in events:
                event_start = event.get('start_at', 0)
                original_start = event_start
                # Handle both timestamp formats (ms or ISO string)
                if isinstance(event_start, str):
                    try:
                        event_start = int(datetime.fromisoformat(event_start.replace('Z', '+00:00')).timestamp() * 1000)
                    except:
                        print(f"DEBUG: Failed to parse date: {original_start}")
                        continue

                print(f"DEBUG: Event '{event.get('title', 'No title')}' start: {event_start}, in range: {since_ms <= event_start <= end_ms}")

                if since_ms <= event_start <= end_ms:
                    filtered_events.append(event)

            print(f"DEBUG: After filtering: {len(filtered_events)} events")
            return filtered_events

        except requests.exceptions.RequestException as e:
            print(f"Error fetching events: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            raise

    def get_public_events(
        self,
        calendar_id: str,
        days_forward: int = 30
    ) -> List[Dict]:
        """
        Fetch events from a public TimeTree calendar (no authentication needed).

        Args:
            calendar_id: The public calendar ID (e.g., 'hbn_187')
            days_forward: Number of days into the future to fetch (default: 30)

        Returns:
            List of event dictionaries
        """
        now = datetime.now()
        from_ms = int(now.timestamp() * 1000)
        to_ms = int((now + timedelta(days=days_forward)).timestamp() * 1000)
        utc_offset = 32400

        url = f"{self.BASE_URL}/api/v2/public_calendars/{calendar_id}/public_events"
        params = {
            'from': from_ms,
            'to': to_ms,
            'utc_offset': utc_offset
        }

        # No authentication needed for public calendars
        response = requests.get(url, params=params, headers={'x-timetreea': 'web/2.1.0/ja'})
        response.raise_for_status()
        data = response.json()

        return data.get('public_events', [])


def main():
    """Example usage of the TimeTree client."""
    # Initialize client
    client = TimeTreeClient()

    # Get calendar ID from environment
    calendar_id = os.getenv('TIMETREE_CALENDAR_ID')
    if not calendar_id:
        print("Error: TIMETREE_CALENDAR_ID not set in .env")
        return

    # Fetch calendars
    print("Fetching calendars...")
    try:
        calendars = client.get_calendars()
        print(f"Found {len(calendars)} calendar(s)")
        for cal in calendars:
            print(f"  - {cal.get('name', 'Untitled')} (ID: {cal.get('id')})")
    except Exception as e:
        print(f"Failed to fetch calendars: {e}")

    # Fetch events
    print(f"\nFetching events from calendar {calendar_id}...")
    try:
        events = client.get_events(calendar_id, days_forward=30)
        print(f"Found {len(events)} event(s)")
        for event in events[:5]:  # Show first 5
            print(f"  - {event.get('title', 'Untitled')}")
            print(f"    Start: {event.get('start_at')}")
            print(f"    End: {event.get('end_at')}")
    except Exception as e:
        print(f"Failed to fetch events: {e}")


if __name__ == "__main__":
    main()
