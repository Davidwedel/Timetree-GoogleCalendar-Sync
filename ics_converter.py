"""
ICS Converter

Converts TimeTree events to ICS (iCalendar) format for import into other calendar applications.
"""

from datetime import datetime
from typing import List, Dict
from icalendar import Calendar, Event as ICSEvent
import pytz


class ICSConverter:
    """Converts TimeTree events to ICS format."""

    @staticmethod
    def parse_timetree_datetime(dt_string: str) -> datetime:
        """
        Parse TimeTree datetime string to datetime object.

        Args:
            dt_string: DateTime string (could be ISO format or timestamp in ms)

        Returns:
            datetime object
        """
        # Try parsing as timestamp (milliseconds)
        try:
            timestamp_ms = int(dt_string)
            return datetime.fromtimestamp(timestamp_ms / 1000, tz=pytz.UTC)
        except (ValueError, TypeError):
            pass

        # Try parsing as ISO format
        try:
            # Handle timezone info
            if 'Z' in dt_string or '+' in dt_string or dt_string.endswith('00:00'):
                return datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
            else:
                return datetime.fromisoformat(dt_string).replace(tzinfo=pytz.UTC)
        except (ValueError, TypeError):
            pass

        # Fallback: return current time
        print(f"Warning: Could not parse datetime: {dt_string}")
        return datetime.now(tz=pytz.UTC)

    @staticmethod
    def convert_to_ics(events: List[Dict], calendar_name: str = "TimeTree Calendar") -> str:
        """
        Convert TimeTree events to ICS format.

        Args:
            events: List of TimeTree event dictionaries
            calendar_name: Name for the calendar

        Returns:
            ICS content as string
        """
        cal = Calendar()
        cal.add('prodid', '-//TimeTree to Google Calendar Sync//EN')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('x-wr-calname', calendar_name)
        cal.add('x-wr-timezone', 'UTC')

        for event_data in events:
            event = ICSEvent()

            # Required fields
            event.add('uid', event_data.get('id', ''))
            event.add('summary', event_data.get('title', 'Untitled Event'))

            # Parse dates
            start_at = ICSConverter.parse_timetree_datetime(event_data.get('start_at', ''))
            end_at = ICSConverter.parse_timetree_datetime(event_data.get('end_at', ''))

            event.add('dtstart', start_at)
            event.add('dtend', end_at)

            # Optional fields
            if event_data.get('note'):
                event.add('description', event_data['note'])

            if event_data.get('location_name'):
                event.add('location', event_data['location_name'])

            if event_data.get('url'):
                event.add('url', event_data['url'])

            # Add timestamp
            event.add('dtstamp', datetime.now(tz=pytz.UTC))

            cal.add_component(event)

        return cal.to_ical().decode('utf-8')

    @staticmethod
    def save_to_file(events: List[Dict], filename: str = "timetree_events.ics") -> str:
        """
        Save events to an ICS file.

        Args:
            events: List of TimeTree event dictionaries
            filename: Output filename

        Returns:
            Path to the saved file
        """
        ics_content = ICSConverter.convert_to_ics(events)

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(ics_content)

        return filename


def main():
    """Example usage."""
    # Example TimeTree event
    sample_events = [
        {
            'id': 'test-event-1',
            'title': 'Test Event',
            'start_at': '2026-03-05T10:00:00Z',
            'end_at': '2026-03-05T11:00:00Z',
            'note': 'This is a test event',
            'location_name': 'Test Location'
        }
    ]

    # Convert to ICS
    ics_content = ICSConverter.convert_to_ics(sample_events)
    print("Generated ICS content:")
    print(ics_content)

    # Save to file
    filename = ICSConverter.save_to_file(sample_events, "test_events.ics")
    print(f"\nSaved to {filename}")


if __name__ == "__main__":
    main()
