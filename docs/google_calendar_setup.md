# Google Calendar API Setup Guide

## Quick Steps

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name (e.g., "TimeTree Sync")
4. Click "Create"

### 2. Enable Google Calendar API

1. In your project, click "APIs & Services" → "Library" (left sidebar)
2. Search for "Google Calendar API"
3. Click on it, then click "Enable"

### 3. Create OAuth Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" user type
   - Fill in app name (e.g., "TimeTree to Google Sync")
   - Add your email as developer contact
   - Skip optional fields
   - Click "Save and Continue" through the scopes and test users screens
4. Back to Create OAuth client ID:
   - Application type: **Desktop app**
   - Name: "TimeTree Sync Desktop"
   - Click "Create"

### 4. Download Credentials

1. After creating, you'll see a dialog with your credentials
2. Click "Download JSON"
3. Save the file as `credentials.json` in your project directory:
   ```bash
   /home/davidwedel/projects/timetreegoogle/credentials.json
   ```

### 5. First Time Authentication

Run the sync script:
```bash
cd /home/davidwedel/projects/timetreegoogle
python sync.py
```

What happens:
1. A browser window will open automatically
2. Sign in with your Google account
3. You'll see a warning "Google hasn't verified this app" - click "Advanced" → "Go to [app name] (unsafe)"
4. Grant permission to "See, edit, share, and permanently delete all calendars you can access using Google Calendar"
5. The browser will show "The authentication flow has completed"
6. Close the browser - the script will continue

A `token.json` file will be created to store your authentication for future runs.

## Testing

After setup, test the connection:

```bash
# List your Google Calendars
python google_calendar_sync.py
```

## Full Sync

Now you can sync TimeTree events to Google Calendar:

```bash
# Sync to primary calendar
python sync.py

# Sync to a specific calendar
python sync.py --google-calendar your.email@gmail.com

# Export to ICS first (to preview events)
python sync.py --output-ics test.ics
```

## Troubleshooting

### "credentials.json not found"
- Make sure you downloaded the JSON file
- Rename it to exactly `credentials.json`
- Place it in the project root directory

### "Access blocked: This app's request is invalid"
- Make sure you selected "Desktop app" not "Web application"
- Recreate the OAuth client ID if needed

### "The authentication flow has completed" but script errors
- Check that Google Calendar API is enabled
- Make sure you granted all permissions
- Try deleting `token.json` and authenticating again

### Permission denied errors
- Delete `token.json`
- Run the script again to re-authenticate
- Make sure to grant all requested permissions

## Security Notes

- `credentials.json` contains your OAuth client ID (not a secret for desktop apps)
- `token.json` contains your access token - keep it private
- Both files are in `.gitignore` to prevent accidental commits
- You can revoke access anytime at https://myaccount.google.com/permissions
