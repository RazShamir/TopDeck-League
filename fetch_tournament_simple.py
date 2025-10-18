#!/usr/bin/env python3
"""
Simple tournament fetcher - just provide tournament ID.
You'll need to copy the curl command from DevTools Network tab once.
"""

import sys
import re
import json
import subprocess

def main():
    if len(sys.argv) < 3:
        print("Usage: python fetch_tournament_simple.py <tournament_id> <encoded_id>")
        print("")
        print("To get the encoded ID:")
        print("1. Open DevTools (F12) → Network tab")
        print("2. Visit the tournament page")
        print("3. Find POST to /arena/tournament")
        print("4. Look at Payload tab, copy the value before last |")
        print("   Example: ...5|5|QhlSGUAAA| → copy 'QhlSGUAAA'")
        print("")
        print("Example:")
        print("  python fetch_tournament_simple.py 4651297216135168 QhlSGUAAA")
        sys.exit(1)

    tournament_id = sys.argv[1]
    encoded_id = sys.argv[2]

    # Load SACSID
    try:
        with open('.sacsid.json', 'r') as f:
            data = json.load(f)
            sacsid = data.get('sacsid', '')
    except Exception as e:
        print(f"Error: Could not read SACSID from .sacsid.json: {e}")
        print("Run: ./update_sacsid.sh <your-sacsid>")
        sys.exit(1)

    if not sacsid:
        print("Error: SACSID is empty in .sacsid.json")
        print("Run: ./update_sacsid.sh <your-sacsid>")
        sys.exit(1)

    print(f"Fetching tournament {tournament_id} with encoded ID {encoded_id}...")

    # Use curl to fetch
    cmd = [
        'curl', '-s',
        'https://mtgarena.appspot.com/arena/tournament',
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

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = result.stdout

        if data.startswith('//OK['):
            print("✓ Success!")

            # Save to file
            output_file = f"tournament_{tournament_id}_data.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(data)
            print(f"Saved to: {output_file}")

            # Parse tournament info and players from the JSON array at the end
            array_match = re.search(r'\[\"com\.snazzorama.*?\](?=,0,7\]$)', data)
            if array_match:
                try:
                    array_data = json.loads(array_match.group(0))

                    # Extract info
                    tournament_name = array_data[4] if len(array_data) > 4 else "Unknown"
                    format_type = array_data[-1] if array_data else "Unknown"

                    # Find players - between "java.lang.String/2004016611" and "[Lcom..."
                    try:
                        str_idx = array_data.index("java.lang.String/2004016611")
                        players = []
                        for item in array_data[str_idx+1:]:
                            if isinstance(item, str) and item.startswith("[L"):
                                break
                            if isinstance(item, str) and item and "@" not in item:
                                players.append(item)

                        print(f"\nTournament: {tournament_name}")
                        print(f"Format: {format_type}")
                        print(f"\nPlayers ({len(players)}):")
                        for i, player in enumerate(players, 1):
                            print(f"  {i}. {player}")
                    except ValueError:
                        pass
                except:
                    pass
        else:
            print(f"✗ Failed: {data[:200]}")
            sys.exit(1)

    except subprocess.TimeoutExpired:
        print("✗ Request timed out")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
