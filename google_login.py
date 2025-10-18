#!/usr/bin/env python3
"""
Google OAuth login to automatically get SACSID cookie for mtgarena.appspot.com
"""

import sys
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

def get_sacsid_via_google_oauth():
    """
    Open browser, login via Google OAuth, and extract SACSID cookie
    """
    print("=" * 70)
    print("Google OAuth Login for MTGA")
    print("=" * 70)
    print("\nThis will open a browser window for you to login.")
    print("Please login with your Google account that has access to mtgarena.appspot.com")
    print("\nPress Enter to continue...")
    input()

    # Set up Chrome in non-headless mode so user can interact
    options = webdriver.ChromeOptions()
    # Don't use headless - we need user interaction
    options.add_argument('--start-maximized')

    driver = None
    try:
        print("\nOpening browser...")
        driver = webdriver.Chrome(options=options)

        # Navigate to MTGA site
        print("Navigating to mtgarena.appspot.com...")
        driver.get('https://mtgarena.appspot.com')

        # Wait for user to complete login
        print("\n" + "=" * 70)
        print("Please complete the login in the browser window.")
        print("Once you're logged in and see the tournament page,")
        print("come back here and press Enter...")
        print("=" * 70)
        input()

        # Get all cookies
        cookies = driver.get_cookies()

        # Find SACSID cookie
        sacsid = None
        for cookie in cookies:
            if cookie['name'] == 'SACSID':
                sacsid = cookie['value']
                break

        if sacsid:
            # Save to .sacsid.json
            with open('.sacsid.json', 'w') as f:
                json.dump({'sacsid': sacsid}, f)

            print("\n✓ SACSID cookie saved successfully!")
            print(f"  Value: {sacsid[:50]}...")
            print(f"  Saved to: .sacsid.json")
            return sacsid
        else:
            print("\n✗ Could not find SACSID cookie")
            print("  Make sure you're logged in successfully")
            return None

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if driver:
            print("\nClosing browser...")
            driver.quit()

def main():
    print("\nStarting Google OAuth login process...")
    sacsid = get_sacsid_via_google_oauth()

    if sacsid:
        print("\n" + "=" * 70)
        print("✓ Login successful!")
        print("=" * 70)
        print("\nYou can now run:")
        print("  ./process_tournament.sh <tournament_id> <encoded_id>")
        sys.exit(0)
    else:
        print("\n" + "=" * 70)
        print("✗ Login failed")
        print("=" * 70)
        print("\nPlease try again or use manual SACSID update:")
        print("  ./update_sacsid.sh YOUR_SACSID")
        sys.exit(1)

if __name__ == '__main__':
    main()
