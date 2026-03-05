"""
TimeTree API Client

This module provides functionality to fetch events from TimeTree calendars
using browser session cookies for authentication.
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv


class TimeTreeClient:
    """Client for interacting with TimeTree's internal API."""

    BASE_URL = "https://timetreeapp.com"

    COOKIE_CACHE_FILE = '.session_cache.json'

    @staticmethod
    def login_with_selenium(email: str, password: str) -> tuple:
        """
        Log in to TimeTree using Selenium and return the session cookie value and expiry.

        Args:
            email: TimeTree account email
            password: TimeTree account password

        Returns:
            Tuple of (cookie_value, expiry_timestamp)
        """
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.firefox.options import Options
        from selenium.webdriver.firefox.service import Service
        from webdriver_manager.firefox import GeckoDriverManager

        options = Options()
        options.add_argument('--headless')
        driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)

        try:
            driver.get('https://timetreeapp.com/signin')

            wait = WebDriverWait(driver, 15)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"], input[name="email"]')))

            driver.find_element(By.CSS_SELECTOR, 'input[type="email"], input[name="email"]').send_keys(email)
            driver.find_element(By.CSS_SELECTOR, 'input[type="password"]').send_keys(password)
            driver.find_element(By.CSS_SELECTOR, 'input[type="password"]').submit()

            # Wait for login to complete (redirects to /calendars/...)
            wait.until(EC.url_contains('/calendars/'))

            cookie = driver.get_cookie('_session_id')
            if not cookie:
                raise ValueError("Login failed - session cookie not found after login")
            return cookie['value'], cookie.get('expiry')
        finally:
            driver.quit()

    def _get_session_cookie(self, email: str, password: str) -> str:
        """Return a valid session cookie, using cache if available."""
        if os.path.exists(self.COOKIE_CACHE_FILE):
            with open(self.COOKIE_CACHE_FILE) as f:
                cache = json.load(f)
            expiry = cache.get('expiry')
            if expiry is None or expiry > time.time():
                print("Using cached session cookie.")
                return cache['value']
            print("Cached session cookie expired, logging in again...")
        else:
            print("No cached session cookie, logging in with Selenium...")

        value, expiry = self.login_with_selenium(email, password)
        with open(self.COOKIE_CACHE_FILE, 'w') as f:
            json.dump({'value': value, 'expiry': expiry}, f)
        print("Login successful.")
        return value

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
            email = os.getenv('TIMETREE_EMAIL')
            password = os.getenv('TIMETREE_PASSWORD')
            if email and password:
                self.session_cookie = self._get_session_cookie(email, password)
            else:
                raise ValueError(
                    "No TimeTree credentials found. "
                    "Set TIMETREE_SESSION_COOKIE or TIMETREE_EMAIL+TIMETREE_PASSWORD in .env"
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
        since: int = 0
    ) -> List[Dict]:
        """
        Fetch events from a specific calendar using delta sync.

        Args:
            calendar_id: The TimeTree calendar ID
            since: Timestamp in milliseconds to fetch changes since (0 = all events)

        Returns:
            List of event dictionaries
        """
        url = f"{self.BASE_URL}/api/v1/calendar/{calendar_id}/events"
        params = {'since': since}

        response = self.session.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        print(f"DEBUG: keys: {list(data.keys())}")
        events = data.get('events', [])
        events = [e for e in events if e.get('deactivated_at') is None]
        return events

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
        events = client.get_events(calendar_id)
        print(f"Found {len(events)} event(s)")
        for event in events[:5]:  # Show first 5
            print(f"  - {event.get('title', 'Untitled')}")
            print(f"    Start: {event.get('start_at')}")
            print(f"    End: {event.get('end_at')}")
    except Exception as e:
        print(f"Failed to fetch events: {e}")


if __name__ == "__main__":
    main()
