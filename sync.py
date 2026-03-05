#!/usr/bin/env python3
"""
TimeTree to Google Calendar Sync

Main script to sync events from TimeTree to Google Calendar.
"""

import os
import argparse
from dotenv import load_dotenv
from timetree_client import TimeTreeClient
from google_calendar_sync import GoogleCalendarSync
from ics_converter import ICSConverter


def main():
    """Main sync function."""
    parser = argparse.ArgumentParser(
        description='Sync TimeTree calendar to Google Calendar'
    )
    parser.add_argument(
        '--calendar-id',
        help='TimeTree calendar ID (overrides .env)',
        default=None
    )
    parser.add_argument(
        '--google-calendar',
        help='Google Calendar ID (default: primary)',
        default=None
    )
    parser.add_argument(
        '--days-forward',
        type=int,
        help='Number of days into the future to sync (default: 30)',
        default=30
    )
    parser.add_argument(
        '--days-back',
        type=int,
        help='Number of days into the past to sync (default: 0)',
        default=0
    )
    parser.add_argument(
        '--output-ics',
        help='Export to ICS file instead of syncing to Google Calendar',
        metavar='FILENAME'
    )
    parser.add_argument(
        '--public',
        help='Use public calendar API (no authentication)',
        action='store_true'
    )
    parser.add_argument(
        '--clear-first',
        help='Clear existing events from Google Calendar before syncing',
        action='store_true'
    )
    parser.add_argument(
        '--list-calendars',
        help='List available TimeTree calendars and exit',
        action='store_true'
    )
    parser.add_argument(
        '--delete-only',
        help='Delete Google Calendar events matching TimeTree event names, without syncing',
        action='store_true'
    )

    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    # Get configuration
    calendar_id = args.calendar_id or os.getenv('TIMETREE_CALENDAR_ID')
    google_calendar_id = args.google_calendar or os.getenv('GOOGLE_CALENDAR_ID', 'primary')

    if not calendar_id and not args.list_calendars:
        print("Error: TimeTree calendar ID not provided.")
        print("Set TIMETREE_CALENDAR_ID in .env or use --calendar-id")
        return 1

    # Initialize TimeTree client
    print("Connecting to TimeTree...")
    try:
        if args.public:
            # For public calendars, we don't need authentication
            print(f"Using public calendar: {calendar_id}")
            client = TimeTreeClient()
            events = client.get_public_events(calendar_id, days_forward=args.days_forward)
        else:
            client = TimeTreeClient()

            # List calendars if requested
            if args.list_calendars:
                print("\nAvailable TimeTree calendars:")
                calendars = client.get_calendars()
                for cal in calendars:
                    print(f"  - {cal.get('name', 'Untitled')} (ID: {cal.get('id')})")
                return 0

            # Fetch events
            print(f"Fetching events from calendar: {calendar_id}")
            events = client.get_events(calendar_id)

    except Exception as e:
        print(f"Error connecting to TimeTree: {e}")
        print("\nTroubleshooting:")
        print("  1. Make sure TIMETREE_SESSION_COOKIE is set in .env")
        print("  2. Check that your session cookie is still valid")
        print("  3. Try using --public flag for public calendars")
        return 1

    if not events:
        print("No events found in the specified time range.")
        return 0

    print(f"Found {len(events)} event(s)")

    # Show first few events
    print("\nPreview of events:")
    for event in events[:5]:
        print(f"  - {event.get('title', 'Untitled')}")
        print(f"    Start: {event.get('start_at')}")

    if len(events) > 5:
        print(f"  ... and {len(events) - 5} more")

    # Delete matching events and exit if --delete-only
    if args.delete_only:
        print(f"\nDeleting matching events from Google Calendar: {google_calendar_id}")
        try:
            sync = GoogleCalendarSync()
            titles = [e.get('title', 'Untitled') for e in events]
            deleted = sync.delete_events_by_titles(google_calendar_id, titles)
            print(f"\nDeleted {deleted} event(s).")
        except Exception as e:
            print(f"\nError deleting events: {e}")
            return 1
        return 0

    # Export to ICS or sync to Google Calendar
    if args.output_ics:
        print(f"\nExporting to ICS file: {args.output_ics}")
        filename = ICSConverter.save_to_file(events, args.output_ics)
        print(f"✓ Saved to {filename}")
        print("\nTo import into Google Calendar:")
        print("  1. Open Google Calendar on desktop")
        print("  2. Go to Settings → Import & Export")
        print("  3. Select the ICS file and choose a calendar")
    else:
        # Sync to Google Calendar
        print(f"\nSyncing to Google Calendar: {google_calendar_id}")

        try:
            sync = GoogleCalendarSync()

            stats = sync.sync_events(
                google_calendar_id,
                events,
                timezone='UTC',
                clear_existing=args.clear_first
            )

            print("\nSync complete!")
            print(f"  Created: {stats['created']}")
            print(f"  Updated: {stats['updated']}")
            print(f"  Skipped: {stats['skipped']}")
            print(f"  Deleted: {stats['deleted']}")
            print(f"  Failed:  {stats['failed']}")
            if args.clear_first:
                print(f"  Cleared: {stats['cleared']}")

        except FileNotFoundError as e:
            print(f"\nError: {e}")
            print("\nTo set up Google Calendar sync:")
            print("  1. Go to https://console.cloud.google.com/")
            print("  2. Create a new project (or select existing)")
            print("  3. Enable Google Calendar API")
            print("  4. Create OAuth 2.0 credentials (Desktop app)")
            print("  5. Download credentials.json to this directory")
            return 1
        except Exception as e:
            print(f"\nError syncing to Google Calendar: {e}")
            return 1

    return 0


if __name__ == "__main__":
    exit(main())
