# TimeTree to Google Calendar Sync

A Python tool to sync events from TimeTree to Google Calendar. Supports both private (authenticated) and public TimeTree calendars.

## Features

- ✅ Fetch events from TimeTree private calendars (using session cookies)
- ✅ Fetch events from TimeTree public calendars (no authentication needed)
- ✅ Export events to ICS format for manual import
- ✅ Direct sync to Google Calendar via API
- ✅ Configurable date ranges (past and future)
- ✅ Command-line interface with multiple options

## Prerequisites

- Python 3.7 or higher
- TimeTree account (for private calendars)
- Google Calendar account
- Google Cloud project with Calendar API enabled (for direct sync)

## Installation

1. **Clone or download this repository**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your configuration (see Configuration section below).

## Configuration

### For TimeTree Private Calendars

1. **Get your session cookie:**
   - Open TimeTree in your browser and log in
   - Open Developer Tools (F12)
   - Go to Application/Storage → Cookies → `https://timetreeapp.com`
   - Copy the value of the `_timetree_session` cookie
   - Add it to `.env`:
     ```
     TIMETREE_SESSION_COOKIE=your_session_cookie_here
     ```

2. **Get your calendar ID:**
   - Open your TimeTree calendar in browser
   - The URL will look like: `https://timetreeapp.com/calendars/CALENDAR_ID`
   - Copy the calendar ID and add to `.env`:
     ```
     TIMETREE_CALENDAR_ID=your_calendar_id_here
     ```

   Or use the `--list-calendars` flag to see all available calendars:
   ```bash
   python sync.py --list-calendars
   ```

### For TimeTree Public Calendars

Public calendars don't require authentication. Just use the `--public` flag and provide the public calendar ID.

### For Google Calendar API (Direct Sync)

1. **Create Google Cloud Project:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one

2. **Enable Google Calendar API:**
   - In your project, go to "APIs & Services" → "Enable APIs and Services"
   - Search for "Google Calendar API" and enable it

3. **Create OAuth Credentials:**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Choose "Desktop app" as application type
   - Download the credentials file

4. **Save credentials:**
   - Rename the downloaded file to `credentials.json`
   - Place it in the project root directory

5. **First run authentication:**
   - On first run, a browser window will open for authentication
   - Sign in with your Google account
   - Grant permissions to the app
   - The token will be saved in `token.json` for future use

## Usage

### Basic Sync to Google Calendar

```bash
python sync.py
```

This will sync events from your TimeTree calendar to your primary Google Calendar.

### Export to ICS File

```bash
python sync.py --output-ics events.ics
```

Export events to an ICS file that can be manually imported into any calendar application.

### Sync Public Calendar

```bash
python sync.py --public --calendar-id hbn_187 --output-ics public_events.ics
```

### List Available Calendars

```bash
python sync.py --list-calendars
```

### Advanced Options

```bash
# Sync last 7 days and next 90 days
python sync.py --days-back 7 --days-forward 90

# Sync to a specific Google Calendar
python sync.py --google-calendar your.email@gmail.com

# Clear existing events before syncing (use with caution!)
python sync.py --clear-first

# Specify calendar ID via command line
python sync.py --calendar-id YOUR_CALENDAR_ID
```

### All Command-Line Options

```
--calendar-id ID          TimeTree calendar ID (overrides .env)
--google-calendar ID      Google Calendar ID (default: primary)
--days-forward N          Days into future to sync (default: 30)
--days-back N             Days into past to sync (default: 0)
--output-ics FILENAME     Export to ICS file instead of syncing
--public                  Use public calendar API
--clear-first             Clear Google Calendar before syncing
--list-calendars          List available TimeTree calendars
```

## Running as a Script

You can make the sync script executable and run it directly:

```bash
chmod +x sync.py
./sync.py --days-forward 60
```

## Scheduling Automatic Syncs

### Linux/Mac (cron)

Add to your crontab (`crontab -e`):

```bash
# Sync every day at 6 AM
0 6 * * * cd /path/to/timetreegoogle && /usr/bin/python3 sync.py
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., daily at 6 AM)
4. Action: Start a program
   - Program: `python`
   - Arguments: `C:\path\to\timetreegoogle\sync.py`
   - Start in: `C:\path\to\timetreegoogle`

## Project Structure

```
timetreegoogle/
├── sync.py                    # Main sync script
├── timetree_client.py         # TimeTree API client
├── google_calendar_sync.py    # Google Calendar integration
├── ics_converter.py           # ICS export functionality
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── .env                      # Your configuration (not in git)
├── credentials.json          # Google OAuth credentials (not in git)
├── token.json               # Google OAuth token (not in git)
└── README.md                # This file
```

## Modules

### `timetree_client.py`

TimeTree API client for fetching events:
- `TimeTreeClient`: Main client class
- `get_calendars()`: List all calendars
- `get_events()`: Fetch events from private calendar
- `get_public_events()`: Fetch events from public calendar

### `google_calendar_sync.py`

Google Calendar integration:
- `GoogleCalendarSync`: Main sync class
- `create_event()`: Create single event
- `sync_events()`: Sync multiple events
- `get_calendars()`: List Google Calendars

### `ics_converter.py`

ICS format conversion:
- `ICSConverter`: Converter class
- `convert_to_ics()`: Convert events to ICS format
- `save_to_file()`: Save events to ICS file

## Troubleshooting

### "TimeTree session cookie not provided"
- Make sure `.env` file exists and contains `TIMETREE_SESSION_COOKIE`
- Check that the cookie value doesn't have extra quotes or spaces

### "TimeTree session cookie expired"
- Session cookies expire after some time
- Log into TimeTree again and get a fresh cookie
- Update `.env` with the new cookie value

### "credentials.json not found"
- Download OAuth credentials from Google Cloud Console
- Save as `credentials.json` in project root

### "Failed to fetch events"
- Check that your calendar ID is correct
- For private calendars, verify your session cookie is valid
- For public calendars, use the `--public` flag

### Events not showing up in Google Calendar
- Check that you're looking at the correct calendar
- Verify the date range includes the events
- Check for errors in the console output

## Important Notes

⚠️ **Session Cookie Security:**
- Keep your `.env` file secure and never commit it to git
- Session cookies provide full access to your TimeTree account
- Cookies expire periodically and need to be refreshed

⚠️ **Terms of Service:**
- This tool uses TimeTree's internal API which is not officially documented
- Use at your own risk
- Consider this for personal use only

⚠️ **Rate Limiting:**
- Be mindful of API rate limits
- Don't run sync too frequently
- Use appropriate date ranges to limit data transfer

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

## License

GNU General Public License v3.0 - See LICENSE file for details

## Acknowledgments

- Inspired by [gc373/timetree-to-google-calendar-converter](https://github.com/gc373/timetree-to-google-calendar-converter)
- Uses TimeTree's internal API (unofficial)
- Google Calendar API integration via official Google libraries
