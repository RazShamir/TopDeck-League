# TopDeck Tournament Processor - Windows Guide

## Setup

### 1. Install Python
- Download Python 3.8+ from https://www.python.org/downloads/
- During installation, check "Add Python to PATH"

### 2. Create Virtual Environment
```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Quick Start

### Step 1: Update Your SACSID Cookie
```cmd
update_sacsid.bat YOUR_SACSID_HERE
```

To get your SACSID:
- Open https://mtgarena.appspot.com in Chrome
- Press F12 → Application → Cookies
- Find SACSID and copy its value

### Step 2: Get the Encoded Tournament ID
1. Visit the tournament page in Chrome
2. Open DevTools (F12) → Network tab
3. Refresh the page
4. Find the POST request to `/arena/tournament`
5. Click on it → Payload tab
6. Copy the value before the last `|`
   - Example payload: `...5|5|QhlSGUAAA|`
   - Copy: `QhlSGUAAA`

### Step 3: Process Tournament Data

**Interactive Mode (Recommended):**
```cmd
process_tournament.bat
```

**Command Line Mode:**
```cmd
process_tournament.bat 4651297216135168 QhlSGUAAA
```

**With Google Sheets Update:**
```cmd
process_tournament.bat 4651297216135168 QhlSGUAAA --update-sheets
```

**Champion Event (2× points):**
```cmd
process_tournament.bat 4651297216135168 QhlSGUAAA --update-sheets --champion
```

## Alternative: Direct Python

If the batch files don't work, you can use Python directly:

```cmd
REM Activate virtual environment first
venv\Scripts\activate

REM Then run the script
python process_tournament_complete.py 4651297216135168 QhlSGUAAA --update-sheets
```

## Google Sheets Setup (Optional)

To enable `--update-sheets`:

1. **Get Google Service Account credentials:**
   - Go to Google Cloud Console
   - Create a Service Account
   - Download JSON credentials
   - Save as `service_account.json` in the project folder

2. **Create `.env` file** (use Notepad):
   ```
   SPREADSHEET_KEY=your_spreadsheet_key_here
   API_TOKEN=208663963Aa!
   SUMMARY_TAB=Summary
   PLAYERS_TAB=Players
   HISTORY_TAB=History
   ```

3. **Share your Google Sheet:**
   - Open your Google Sheet
   - Click Share
   - Add the service account email (from JSON file)
   - Give it Editor access

## Troubleshooting

**"python is not recognized"**
- Reinstall Python and check "Add Python to PATH"
- Or use full path: `C:\Python39\python.exe`

**"No module named 'gspread'"**
- Activate venv: `venv\Scripts\activate`
- Install dependencies: `pip install -r requirements.txt`

**"SACSID cookie is missing"**
- Run `update_sacsid.bat YOUR_SACSID` first

**"Failed to fetch tournament"**
- SACSID may be expired - get a fresh one from browser
- Check that you're logged into mtgarena.appspot.com

## What You Get

The script will:
1. ✓ Fetch tournament data from MTGA
2. ✓ Parse player names (supports Hebrew/Unicode)
3. ✓ Calculate league points based on placement
4. ✓ Display formatted results
5. ✓ Optionally update Google Sheets

## Example Output

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
...

Prize Pool Increment: +100 NIS
======================================================================
```

## Support

For issues, check:
- QUICK_START_GUIDE.md - General usage
- README.md - Full documentation
- SOLUTION_SUMMARY.md - Technical details
