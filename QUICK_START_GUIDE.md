# TopDeck Tournament Fetcher - Quick Start

## Simple 3-Step Process

### Step 1: Login to MTGA

**Option A: Automatic (Recommended)**
```bash
# Linux/Mac
./login.sh

# Windows
login.bat
```
This opens a browser for Google login and automatically saves your SACSID.

**Option B: Manual**
```bash
./update_sacsid.sh YOUR_SACSID_HERE
```

To get SACSID manually:
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

**Easy Copy-Paste:** You can paste the full tournament URL from your browser!

```bash
python process_tournament_complete.py <tournament_url_or_id> <encoded_id>
```

**Supported URL formats:**
- Full URL: `https://mtgarena.appspot.com/#t4651297216135168`
- Hash format: `#t4651297216135168`
- Short format: `t4651297216135168`
- Numeric ID: `4651297216135168`

Example (dry-run, no sheets update):
```bash
# Easy copy-paste from browser
python process_tournament_complete.py https://mtgarena.appspot.com/#t4651297216135168 QhlSGUAAA

# Or use numeric ID
python process_tournament_complete.py 4651297216135168 QhlSGUAAA
```

To update Google Sheets:
```bash
python process_tournament_complete.py https://mtgarena.appspot.com/#t4651297216135168 QhlSGUAAA --update-sheets
```

For Champion events (2× points):
```bash
python process_tournament_complete.py #t4651297216135168 QhlSGUAAA --update-sheets --champion
```

## Alternative: Extract Encoded ID from cURL

If you copied the request as cURL:
```bash
echo "PASTE_CURL_HERE" | ./extract_from_curl.sh
```

This will show you the encoded ID to use.

## Windows Users

**See [WINDOWS_GUIDE.md](WINDOWS_GUIDE.md) for detailed Windows instructions.**

Quick reference:
- Use `process_tournament.bat` instead of `./process_tournament.sh`
- Use `update_sacsid.bat` instead of `./update_sacsid.sh`
- Use `python` instead of `python3`
- Use `venv\Scripts\activate` instead of `source venv/bin/activate`

Example:
```cmd
update_sacsid.bat YOUR_SACSID
process_tournament.bat https://mtgarena.appspot.com/#t4651297216135168 QhlSGUAAA --update-sheets
```

## Troubleshooting

**"No SACSID found"**
→ Run `./update_sacsid.sh` first

**"HTTP 500 error"**
→ SACSID expired, get a fresh one from your browser

**"Could not find encoded ID"**
→ Make sure you're logged in and the tournament exists

## What You Get

The script will:
1. Fetch and save tournament data to `tournament_<ID>_data.txt`
2. Parse tournament name, format, and player list
3. Calculate league points for each player based on placement
4. Display formatted results with:
   - Tournament details
   - Each player's placement and points earned
   - Prize pool increment (5 NIS per player)
5. Optionally update Google Sheets with:
   - Player points added to Players tab
   - Prize pool increment in Summary tab
   - Tournament history logged

## Google Sheets Setup (Optional)

To enable `--update-sheets`, you need:
1. Google Service Account credentials saved as `service_account.json`
2. Environment variables in `.env`:
   ```
   SPREADSHEET_KEY=your_spreadsheet_key_here
   SUMMARY_TAB=Summary
   PLAYERS_TAB=Players
   HISTORY_TAB=History
   ```

See `README.md` for full setup instructions.

## Alternative: Simple Fetch Only

If you only want to fetch tournament data without processing:
```bash
python fetch_tournament_simple.py 4651297216135168 QhlSGUAAA
```
