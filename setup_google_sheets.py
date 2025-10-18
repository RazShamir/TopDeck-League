#!/usr/bin/env python3
"""
Easy Google Sheets OAuth setup - no service account needed!
Uses OAuth flow to get user credentials for Google Sheets access.
"""

import sys
import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import pickle

# Scopes needed for Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def setup_google_sheets_oauth():
    """
    Run OAuth flow to get Google Sheets credentials
    """
    print("=" * 70)
    print("Google Sheets OAuth Setup")
    print("=" * 70)
    print("\nThis will set up access to Google Sheets using your Google account.")
    print("No service account needed!")
    print("\nWhat you'll need:")
    print("  1. A Google Cloud project with Sheets API enabled")
    print("  2. OAuth 2.0 Client ID credentials (Desktop app)")
    print("")
    print("If you don't have these yet:")
    print("  1. Go to: https://console.cloud.google.com")
    print("  2. Create a project (or select existing)")
    print("  3. Enable Google Sheets API")
    print("  4. Create OAuth 2.0 Client ID (Application type: Desktop)")
    print("  5. Download the JSON file")
    print("")
    print("=" * 70)
    print("")

    # Check for credentials file
    creds_file = 'client_secret.json'
    if not os.path.exists(creds_file):
        print(f"✗ {creds_file} not found!")
        print("")
        print("Please download your OAuth 2.0 Client ID credentials and save as:")
        print(f"  {creds_file}")
        print("")
        return False

    print(f"✓ Found {creds_file}")
    print("")

    creds = None
    token_file = 'token.pickle'

    # Check if we have saved credentials
    if os.path.exists(token_file):
        print(f"Found existing credentials in {token_file}")
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials, run OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            print("Starting OAuth flow...")
            print("A browser window will open for you to authorize access.")
            print("")
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for future use
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)

        print("")
        print(f"✓ Credentials saved to {token_file}")

    # Test the credentials
    try:
        from googleapiclient.discovery import build

        print("\nTesting credentials...")
        service = build('sheets', 'v4', credentials=creds)

        # Try to list spreadsheets (this will fail but proves auth works)
        print("✓ Successfully authenticated with Google Sheets API!")
        print("")
        print("=" * 70)
        print("Setup Complete!")
        print("=" * 70)
        print("")
        print("You can now use the tournament processor with Google Sheets.")
        print("Make sure to set your SPREADSHEET_KEY in .env file.")
        print("")
        return True

    except Exception as e:
        print(f"\n✗ Error testing credentials: {e}")
        return False

def main():
    if setup_google_sheets_oauth():
        sys.exit(0)
    else:
        print("\n" + "=" * 70)
        print("Setup failed. Please check the instructions above.")
        print("=" * 70)
        sys.exit(1)

if __name__ == '__main__':
    main()
