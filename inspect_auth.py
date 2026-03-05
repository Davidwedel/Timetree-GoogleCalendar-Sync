#!/usr/bin/env python3
"""
Interactive tool to help find TimeTree authentication tokens.

This script will help you inspect network requests to understand
what authentication TimeTree is using.
"""

import json


def main():
    print("=" * 60)
    print("TimeTree Authentication Inspector")
    print("=" * 60)
    print()
    print("Let's find the authentication headers TimeTree uses.")
    print()
    print("STEPS TO FOLLOW:")
    print()
    print("1. Open TimeTree in your browser (https://timetreeapp.com)")
    print("   and log in to your account")
    print()
    print("2. Open Developer Tools:")
    print("   - Chrome/Edge: Press F12 or Ctrl+Shift+I")
    print("   - Firefox: Press F12 or Ctrl+Shift+K")
    print("   - Safari: Cmd+Option+I")
    print()
    print("3. Go to the NETWORK tab in DevTools")
    print()
    print("4. Make sure 'Preserve log' is checked")
    print()
    print("5. Navigate to your calendar or refresh the page")
    print()
    print("6. Look for requests to:")
    print("   - timetreeapp.com/api/")
    print("   - Any request with 'calendar' or 'event' in the URL")
    print()
    print("7. Click on one of these requests")
    print()
    print("8. Look at the 'Headers' tab, find 'Request Headers'")
    print()
    print("9. Copy ALL the headers you see there")
    print()
    print("-" * 60)
    print()
    print("WHAT TO LOOK FOR:")
    print()
    print("Common authentication methods TimeTree might use:")
    print()
    print("  ✓ Cookie: header with '_timetree_session=...'")
    print("  ✓ Authorization: Bearer <token>")
    print("  ✓ X-Auth-Token: <token>")
    print("  ✓ X-TimeTree-Token: <token>")
    print("  ✓ Any other X-* custom headers")
    print()
    print("-" * 60)
    print()
    print("EXAMPLE - What you might see:")
    print()
    print("Request URL: https://timetreeapp.com/api/v2/calendars")
    print("Request Headers:")
    print("  Accept: application/json")
    print("  Authorization: Bearer eyJhbGc...")
    print("  Cookie: _timetree_session=abc123...")
    print("  User-Agent: Mozilla/5.0...")
    print("  x-timetreea: web/2.1.0/ja")
    print()
    print("-" * 60)
    print()

    # Get user input
    print("Now, let's analyze what you found:")
    print()
    print("Paste the request headers here (or type 'skip' to see other options):")
    print("(Paste everything, then press Enter twice when done)")
    print()

    lines = []
    empty_count = 0

    while empty_count < 2:
        try:
            line = input()
            if line.strip() == 'skip':
                show_alternatives()
                return
            if not line.strip():
                empty_count += 1
            else:
                empty_count = 0
                lines.append(line)
        except EOFError:
            break

    if not lines:
        show_alternatives()
        return

    # Analyze the headers
    print()
    print("=" * 60)
    print("ANALYSIS:")
    print("=" * 60)
    print()

    headers_text = '\n'.join(lines)
    found_auth = False

    # Check for common auth patterns
    if '_timetree_session' in headers_text.lower():
        print("✓ Found: _timetree_session cookie")
        # Try to extract it
        for line in lines:
            if '_timetree_session' in line.lower():
                print(f"  Line: {line}")
                if '=' in line:
                    parts = line.split('=', 1)
                    if len(parts) > 1:
                        value = parts[1].split(';')[0].strip()
                        print(f"  Value: {value[:50]}..." if len(value) > 50 else f"  Value: {value}")
        found_auth = True
        print()

    if 'authorization:' in headers_text.lower():
        print("✓ Found: Authorization header")
        for line in lines:
            if 'authorization:' in line.lower():
                print(f"  {line}")
        found_auth = True
        print()

    if 'x-auth' in headers_text.lower() or 'x-timetree' in headers_text.lower():
        print("✓ Found: Custom authentication header")
        for line in lines:
            if 'x-auth' in line.lower() or 'x-timetree' in line.lower():
                print(f"  {line}")
        found_auth = True
        print()

    if not found_auth:
        print("⚠ No obvious authentication found in the headers you provided.")
        print()
        print("This could mean:")
        print("  1. The headers weren't complete")
        print("  2. TimeTree uses a different auth method")
        print("  3. You might need to look at a different request")
        print()
        show_alternatives()


def show_alternatives():
    print()
    print("=" * 60)
    print("ALTERNATIVE APPROACHES:")
    print("=" * 60)
    print()
    print("1. CURL EXPORT METHOD:")
    print("   - In Network tab, right-click on a request")
    print("   - Select 'Copy' → 'Copy as cURL'")
    print("   - Paste it into a file and look for auth headers")
    print()
    print("2. USE PUBLIC CALENDAR:")
    print("   - If your calendar is public, no auth needed!")
    print("   - Use: python sync.py --public --calendar-id YOUR_ID")
    print()
    print("3. BROWSER STORAGE:")
    print("   - DevTools → Application → Storage")
    print("   - Check Local Storage, Session Storage")
    print("   - Look for 'token', 'auth', 'session' keys")
    print()
    print("4. INSPECT NETWORK REQUEST:")
    print("   - Look at a request in Network tab")
    print("   - Check both 'Headers' and 'Cookies' tabs")
    print("   - Some browsers separate cookie display")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting...")
