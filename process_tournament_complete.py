#!/usr/bin/env python3
"""
Complete tournament processor: fetch, parse, calculate points, display results, and update sheets.
Uses the working curl-based fetch method with encoded tournament ID.
"""

import sys
import re
import json
import subprocess
import os
from typing import List, Dict, Optional
from parse_tournament_url import parse_tournament_url

# Load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If dotenv not available, try manual .env loading
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

def fetch_tournament_data(tournament_id: str, encoded_id: str, sacsid: str) -> str:
    """Fetch raw tournament data using curl (proven working method)"""
    url = 'https://mtgarena.appspot.com/arena/tournament'

    cmd = [
        'curl', '-s', url,
        '-H', 'accept: */*',
        '-H', 'content-type: text/x-gwt-rpc; charset=UTF-8',
        '-b', f'SACSID={sacsid}',
        '-H', 'origin: https://mtgarena.appspot.com',
        '-H', 'referer: https://mtgarena.appspot.com/',
        '-H', 'user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        '-H', 'x-gwt-module-base: https://mtgarena.appspot.com/arena/',
        '-H', 'x-gwt-permutation: 79B8599238A9627852278DC457BF90AA',
        '--data-raw', f'7|0|5|https://mtgarena.appspot.com/arena/|F9916789951930449A4C1B88925C3ACF|com.snazzorama.arena.client.TournamentService|getTournament|java.lang.Long/4227064769|1|2|3|4|1|5|5|{encoded_id}|'
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    if result.returncode == 0 and result.stdout.startswith('//OK['):
        return result.stdout
    else:
        raise Exception(f"Failed to fetch: {result.stdout[:200]}")

def parse_tournament_data(data: str) -> tuple:
    """Parse tournament name, format, and players from GWT-RPC response"""
    array_match = re.search(r'\[\"com\.snazzorama.*?\](?=,0,7\]$)', data)
    if not array_match:
        raise Exception("Could not parse tournament data")

    # Parse JSON with proper escape handling
    json_str = array_match.group(0)

    # Replace hex escapes like \x27 with proper JSON escapes
    # \x27 is apostrophe ('), which JSON needs as \'
    def replace_hex(match):
        hex_val = match.group(1)
        char_code = int(hex_val, 16)
        return chr(char_code)

    # Replace \xNN sequences with actual characters
    json_str = re.sub(r'\\x([0-9a-fA-F]{2})', replace_hex, json_str)

    array_data = json.loads(json_str)

    # Extract tournament info
    tournament_name = array_data[4] if len(array_data) > 4 else "Unknown Tournament"
    format_type = array_data[-1] if array_data else "Unknown Format"

    # Find players - between "java.lang.String/2004016611" and "[Lcom..."
    try:
        str_idx = array_data.index("java.lang.String/2004016611")
        players = []
        for item in array_data[str_idx+1:]:
            if isinstance(item, str) and item.startswith("[L"):
                break
            if isinstance(item, str) and item and "@" not in item:
                players.append(item)

        return tournament_name, format_type, players
    except ValueError:
        raise Exception("Could not parse player list")

def calculate_league_points(players: List[str], is_champion: bool = False) -> Dict[str, int]:
    """
    Calculate league points for each player based on placement.

    Scoring rules:
    - Everyone: +1 participation
    - 1st: +4 additional
    - 2nd: +3 additional
    - 3rd-4th: +2 additional (if 21+ players) or +1 (if fewer)
    - 5th-8th: +1 additional (if 21+ players)
    - 5th-6th: +1 additional (if 16-20 players)
    - Champion events: All points doubled
    """
    points = {}
    num_players = len(players)

    for i, player in enumerate(players, 1):
        # Base participation point
        player_points = 1

        # Placement bonuses
        if i == 1:
            player_points += 4
        elif i == 2:
            player_points += 3
        elif i in [3, 4]:
            if num_players >= 21:
                player_points += 2
            else:
                player_points += 1
        elif i in [5, 6, 7, 8]:
            if num_players >= 21:
                player_points += 1
            elif num_players >= 16 and i in [5, 6]:
                player_points += 1

        # Double for champion events
        if is_champion:
            player_points *= 2

        points[player] = player_points

    return points

def calculate_prize_pool(num_players: int, per_player_nis: int = 5) -> int:
    """Calculate prize pool increment"""
    return num_players * per_player_nis

def display_results(tournament_name: str, format_type: str, players: List[str],
                   points: Dict[str, int], prize_pool: int, is_champion: bool):
    """Display formatted tournament results"""
    print("\n" + "=" * 70)
    print("TOURNAMENT RESULTS & LEAGUE POINTS")
    print("=" * 70)
    print(f"\nTournament: {tournament_name}")
    print(f"Format: {format_type}")
    print(f"Players: {len(players)}")
    if is_champion:
        print("Event Type: CHAMPION (2× points)")
    print(f"\n{'Player':<25} {'Placement':<12} {'Points Earned'}")
    print("-" * 70)

    for i, player in enumerate(players, 1):
        player_points = points[player]
        multiplier = " (×2)" if is_champion else ""
        print(f"{player:<25} #{i:<11} +{player_points} points{multiplier}")

    print(f"\nPrize Pool Increment: +{prize_pool} NIS")
    print("=" * 70)

def update_google_sheets(tournament_id: str, tournament_name: str, players: List[str],
                        points: Dict[str, int], prize_pool: int, is_champion: bool):
    """Update Google Sheets with tournament results"""
    try:
        from sheets_io import open_ws, ensure_summary, update_prize_pool
        from sheets_io import ensure_history, append_history_row, history_has_tournament
        from name_match import match_or_new
        from sheets_io import upsert_points
        from datetime import datetime

        spreadsheet_key = os.getenv("SPREADSHEET_KEY")
        if not spreadsheet_key:
            print("\n✗ SPREADSHEET_KEY not set in .env file")
            return False

        summary_tab = os.getenv("SUMMARY_TAB", "Summary")
        history_tab = os.getenv("HISTORY_TAB", "History")
        players_tab = os.getenv("PLAYERS_TAB", "Players")

        print("\n" + "-" * 70)
        print("Updating Google Sheets...")

        # Check if tournament already processed (idempotency)
        hist_ws = open_ws(spreadsheet_key, history_tab)
        ensure_history(hist_ws, hebrew=False)

        if history_has_tournament(hist_ws, tournament_id):
            print(f"⚠ Tournament {tournament_id} already processed (found in history)")
            print("  Skipping to prevent duplicate updates")
            return False

        # Update player points
        players_ws = open_ws(spreadsheet_key, players_tab)
        from sheets_io import ensure_players_header
        ensure_players_header(players_ws)
        upsert_points(players_ws, points, match_or_new)
        print(f"✓ Updated {len(points)} player scores in '{players_tab}' tab")

        # Update prize pool
        summary_ws = open_ws(spreadsheet_key, summary_tab)
        ensure_summary(summary_ws)
        update_prize_pool(summary_ws, prize_pool)
        print(f"✓ Added {prize_pool} NIS to prize pool in '{summary_tab}' tab")

        # Add to history
        timestamp = datetime.now().isoformat()
        top8 = ",".join(players[:8])
        history_row = [
            timestamp,
            tournament_id,
            "Yes",  # IsLeague
            "Yes" if is_champion else "No",  # IsChampion
            str(len(players)),  # Participants
            str(prize_pool),  # PrizeAddedNIS
            top8,  # Top8CSV
            tournament_name  # Note
        ]
        append_history_row(hist_ws, history_row)
        print(f"✓ Added tournament to history in '{history_tab}' tab")

        print("-" * 70)
        print("✓ Google Sheets updated successfully!")
        return True

    except ImportError as e:
        print(f"\n✗ Missing required modules: {e}")
        print("  Make sure gspread and other dependencies are installed")
        return False
    except FileNotFoundError:
        print("\n✗ service_account.json not found")
        print("  You need Google Service Account credentials to update sheets")
        return False
    except Exception as e:
        print(f"\n✗ Failed to update sheets: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    if len(sys.argv) < 3:
        print("=" * 70)
        print("TopDeck Tournament Processor - Interactive Mode")
        print("=" * 70)
        print("")
        print("This script fetches MTGA tournament data and calculates league points.")
        print("")
        print("📋 QUICK START GUIDE:")
        print("")
        print("Step 1: Get your SACSID cookie")
        print("  • Open https://mtgarena.appspot.com in your browser")
        print("  • Press F12 → Application → Cookies")
        print("  • Find SACSID and copy its value")
        print("  • Run: ./update_sacsid.sh YOUR_SACSID")
        print("")
        print("Step 2: Get the encoded tournament ID")
        print("  • Visit the tournament page")
        print("  • Open DevTools (F12) → Network tab")
        print("  • Find POST request to /arena/tournament")
        print("  • Click Payload tab")
        print("  • Copy the value before the last | (e.g., QhlSGUAAA)")
        print("")
        print("Step 3: Run the script")
        print("  ./process_tournament.sh <tournament_url_or_id> <encoded_id>")
        print("")
        print("Supported URL formats:")
        print("  • https://mtgarena.appspot.com/#t4651297216135168")
        print("  • #t4651297216135168")
        print("  • t4651297216135168")
        print("  • 4651297216135168")
        print("")
        print("=" * 70)
        print("")

        # Check if SACSID is configured
        try:
            with open('.sacsid.json', 'r') as f:
                sacsid = json.load(f).get('sacsid', '')
                if sacsid:
                    print("✓ SACSID cookie is configured")
                else:
                    print("✗ SACSID cookie is missing - run ./update_sacsid.sh first")
        except:
            print("✗ SACSID cookie is missing - run ./update_sacsid.sh first")

        print("")
        print("Would you like to process a tournament? (y/n): ", end='')
        try:
            response = input().strip().lower()
            if response == 'y':
                print("")
                print("Enter tournament URL or ID (e.g., https://mtgarena.appspot.com/#t4651297216135168): ", end='')
                tournament_url = input().strip()
                tournament_id, _ = parse_tournament_url(tournament_url)
                print("Enter encoded ID (from DevTools, e.g., QhlSGUAAA): ", end='')
                encoded_id = input().strip()
                print("Update Google Sheets? (y/n): ", end='')
                update_sheets = input().strip().lower() == 'y'
                print("Is this a Champion event (2× points)? (y/n): ", end='')
                is_champion = input().strip().lower() == 'y'

                # Build argv for processing
                sys.argv = ['process_tournament_complete.py', tournament_id, encoded_id]
                if update_sheets:
                    sys.argv.append('--update-sheets')
                if is_champion:
                    sys.argv.append('--champion')

                print("")
                # Continue to processing
            else:
                print("")
                print("Examples:")
                print("  ./process_tournament.sh https://mtgarena.appspot.com/#t4651297216135168 QhlSGUAAA")
                print("  ./process_tournament.sh 4651297216135168 QhlSGUAAA --update-sheets")
                print("  ./process_tournament.sh #t4651297216135168 QhlSGUAAA --update-sheets --champion")
                sys.exit(0)
        except (KeyboardInterrupt, EOFError):
            print("\n\nExiting...")
            sys.exit(0)

    # Parse tournament URL or ID
    tournament_id, _ = parse_tournament_url(sys.argv[1])
    encoded_id = sys.argv[2]
    update_sheets = '--update-sheets' in sys.argv
    is_champion = '--champion' in sys.argv

    # Load SACSID
    try:
        with open('.sacsid.json', 'r') as f:
            sacsid = json.load(f).get('sacsid', '')
            if not sacsid:
                raise ValueError("Empty SACSID")
    except Exception as e:
        print(f"✗ Error: Could not read SACSID: {e}")
        print("\nRun: ./update_sacsid.sh <your-sacsid>")
        print("\nTo get your SACSID:")
        print("  1. Open https://mtgarena.appspot.com in Chrome")
        print("  2. Press F12 → Application → Cookies")
        print("  3. Find SACSID and copy its value")
        sys.exit(1)

    print("=" * 70)
    print("TopDeck Tournament Processor")
    print("=" * 70)
    print(f"Tournament ID: {tournament_id}")
    print(f"Encoded ID: {encoded_id}")
    print(f"Update Sheets: {'Yes' if update_sheets else 'No (dry-run)'}")
    print(f"Champion Event: {'Yes (2× points)' if is_champion else 'No'}")

    # Fetch tournament data
    print("\nFetching tournament data...")
    try:
        raw_data = fetch_tournament_data(tournament_id, encoded_id, sacsid)
        print("✓ Data retrieved")

        # Save raw data for debugging
        output_file = f"tournament_{tournament_id}_data.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(raw_data)
        print(f"✓ Raw data saved to: {output_file}")
    except Exception as e:
        print(f"✗ Failed: {e}")
        sys.exit(1)

    # Parse tournament data
    print("\nParsing tournament data...")
    try:
        tournament_name, format_type, players = parse_tournament_data(raw_data)
        print(f"✓ Found {len(players)} players")
    except Exception as e:
        print(f"✗ Failed to parse: {e}")
        sys.exit(1)

    # Calculate points and prize pool
    points = calculate_league_points(players, is_champion)
    prize_pool = calculate_prize_pool(len(players))

    # Display results
    display_results(tournament_name, format_type, players, points, prize_pool, is_champion)

    # Update Google Sheets if requested
    if update_sheets:
        success = update_google_sheets(tournament_id, tournament_name, players, points,
                                       prize_pool, is_champion)
        if not success:
            print("\n⚠ Sheets update failed, but results are displayed above")
    else:
        print("\n💡 To update Google Sheets, run with --update-sheets flag")

    print("\n" + "=" * 70)
    print("✓ Processing complete!")
    print("=" * 70)

if __name__ == '__main__':
    main()
