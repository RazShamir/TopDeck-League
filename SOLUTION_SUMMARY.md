# TopDeck Tournament Processor - Complete Solution

## Overview

Successfully implemented a complete tournament processing system that fetches Magic: The Gathering Arena tournament data, calculates league points, and optionally updates Google Sheets.

## The Problem

The MTGA website (mtgarena.appspot.com) uses Google Web Toolkit (GWT) RPC protocol which requires:
1. Valid SACSID session cookie from Google OAuth
2. Tournament IDs encoded in GWT's proprietary base64 format
3. Specific GWT-RPC payload structure

The encoded tournament ID (e.g., "QhlSGUAAA" for tournament 4651297216135168) cannot be reverse-engineered easily, so it must be extracted from the browser's network traffic.

## The Solution

### Core Components

1. **process_tournament_complete.py** - Main tournament processor
   - Fetches tournament data using curl subprocess
   - Parses GWT-RPC response to extract tournament info and players
   - Calculates league points based on placement
   - Displays formatted, human-readable results
   - Optionally updates Google Sheets with results

2. **fetch_tournament_simple.py** - Standalone data fetcher
   - Quick fetch-only tool for retrieving tournament data
   - Saves raw data to file for later processing

3. **extract_from_curl.sh** - Helper script
   - Extracts encoded tournament ID from browser's "Copy as cURL" output

4. **update_sacsid.sh** - Cookie management
   - Stores SACSID cookie for authentication

### Workflow

```
1. Get SACSID cookie from browser
   ↓
2. Save with update_sacsid.sh
   ↓
3. Get encoded tournament ID from DevTools Network tab
   ↓
4. Run process_tournament_complete.py
   ↓
5. View formatted results and/or update Google Sheets
```

## Usage Examples

### Basic Usage (Dry-run)
```bash
python3 process_tournament_complete.py 4651297216135168 QhlSGUAAA
```

Output:
```
======================================================================
TOURNAMENT RESULTS & LEAGUE POINTS
======================================================================

Tournament: RTMS Pokemon Tourny Oct 18
Format: Limited: Draft
Players: 20

Player                    Placement    Points Earned
----------------------------------------------------------------------
Jake P                    #1           +5 points
Chase C                   #2           +4 points
Carson  B                 #3           +2 points
William F                 #4           +2 points
[... 16 more players ...]

Prize Pool Increment: +100 NIS
======================================================================
```

### Update Google Sheets
```bash
python3 process_tournament_complete.py 4651297216135168 QhlSGUAAA --update-sheets
```

### Champion Event (2× Points)
```bash
python3 process_tournament_complete.py 4651297216135168 QhlSGUAAA --update-sheets --champion
```

## League Scoring Rules

Implemented in `calculate_league_points()`:

**Base Points:**
- All participants: +1 point

**Placement Bonuses:**
- 1st place: +4 points
- 2nd place: +3 points
- 3rd-4th place: +2 points (if 21+ players) or +1 point (if fewer)
- 5th-8th place: +1 point (if 21+ players)
- 5th-6th place: +1 point (if 16-20 players)

**Champion Events:**
- All points doubled

**Prize Pool:**
- 5 NIS per participant

## Technical Details

### GWT-RPC Protocol

The MTGA API uses GWT-RPC which requires a specific payload format:
```
7|0|5|https://mtgarena.appspot.com/arena/|F9916789951930449A4C1B88925C3ACF|com.snazzorama.arena.client.TournamentService|getTournament|java.lang.Long/4227064769|1|2|3|4|1|5|5|QhlSGUAAA|
```

Key components:
- `F9916789951930449A4C1B88925C3ACF` - GWT strong name
- `79B8599238A9627852278DC457BF90AA` - GWT permutation (in header)
- `QhlSGUAAA` - Encoded tournament ID (must be extracted from browser)

### Response Parsing

The GWT-RPC response format:
```
//OK[32,31,4,0,0,...,["com.snazzorama.arena.client.Tournament/2032815254",...]]
```

We extract the JSON array at the end containing:
- Tournament metadata (name, format, etc.)
- Player list (after "java.lang.String/2004016611" marker)
- Round data (after "[Lcom.snazzorama.arena.client.Tournament$RoundData;" marker)

### Why curl Instead of requests?

The `subprocess + curl` approach was chosen over Python's `requests` library because:
1. Exact header matching with browser's request
2. Proven working solution from manual testing
3. Avoids potential SSL/TLS differences between curl and requests
4. Simpler debugging by matching browser exactly

## Google Sheets Integration

When `--update-sheets` is used, the script:

1. **Updates Players Tab:**
   - Adds points to each player's total
   - Creates new player rows if needed
   - Uses fuzzy name matching for Hebrew names

2. **Updates Summary Tab:**
   - Increments prize pool total

3. **Updates History Tab:**
   - Logs tournament details with timestamp
   - Records top 8 players (CSV format)
   - Prevents duplicate processing (idempotent)

### Required Setup

1. **service_account.json** - Google Service Account credentials
2. **.env file:**
   ```
   SPREADSHEET_KEY=your_spreadsheet_key
   SUMMARY_TAB=Summary
   PLAYERS_TAB=Players
   HISTORY_TAB=History
   ```

## File Structure

```
TopDeckProject/
├── process_tournament_complete.py    # Main processor (NEW)
├── fetch_tournament_simple.py        # Simple fetcher
├── extract_from_curl.sh             # ID extractor
├── update_sacsid.sh                 # Cookie updater
├── test_tournament.sh               # Test script
├── mtga_fetch.py                    # GWT-RPC utilities
├── league_logic.py                  # Points calculation
├── sheets_io.py                     # Google Sheets I/O
├── name_match.py                    # Fuzzy name matching
├── .sacsid.json                     # Stored SACSID cookie
├── .env                             # Environment config
└── QUICK_START_GUIDE.md            # User guide
```

## Testing

Run the test script to verify everything works:
```bash
./test_tournament.sh
```

This will:
1. Process the sample tournament in regular mode
2. Process the same tournament in champion mode (2× points)
3. Show the difference in output

## Limitations & Known Issues

1. **Manual Encoded ID:** Cannot automatically derive GWT's encoded tournament ID. Must be extracted from browser DevTools.

2. **Session Expiration:** SACSID cookies expire after ~24 hours. Must be refreshed from browser.

3. **No Auto-Standings:** Final standings must match the order players finished. If tournament data doesn't include placement info, manual ordering required.

4. **Google OAuth Limitation:** SACSID from Google OAuth login may have limited API permissions compared to classic cookie-based auth.

## Success Metrics

✅ Successfully fetches tournament data
✅ Parses 20-player tournament correctly
✅ Calculates league points with proper rules
✅ Displays human-readable formatted output
✅ Handles champion events (2× points)
✅ Calculates prize pool (5 NIS/player)
✅ Cross-platform compatible (Linux/Windows)
✅ Idempotent sheets updates (prevents duplicates)
✅ Includes comprehensive error handling

## Future Enhancements

- [ ] Automatic encoded ID extraction via browser automation
- [ ] Web UI for tournament processing
- [ ] Support for manual standings entry when auto-detection fails
- [ ] Batch processing multiple tournaments
- [ ] Export results to PDF/CSV
- [ ] Historical statistics and analytics

## Credits

Built for TopDeck League management system.
Developed through iterative problem-solving to handle GWT-RPC protocol challenges.
