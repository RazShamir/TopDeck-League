# TopDeck Tournament Processor

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A complete tournament management system for Magic: The Gathering Arena tournaments. Fetches tournament data, calculates league points, and automatically updates Google Sheets.

## Features

✅ **Easy Copy-Paste URLs** - Paste tournament URLs directly from your browser
✅ **Tournament Data Fetching** - Retrieves MTGA tournament data via GWT-RPC protocol
✅ **League Points Calculator** - Automatic points calculation based on placement
✅ **Google Sheets Integration** - Auto-updates player scores, prize pools, and history
✅ **One-Click OAuth Login** - Automatic Google login for both MTGA and Sheets
✅ **Hebrew Support** - Fully supports Hebrew player names
✅ **Champion Events** - 2× points multiplier for special tournaments
✅ **Cross-Platform** - Works on Windows, Linux, and macOS
✅ **Interactive Mode** - User-friendly prompts for easy operation
✅ **Idempotent Updates** - Prevents duplicate tournament processing

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Set Up Authentication

**Option A: Automatic Google Login (Recommended)**
```bash
# Linux/Mac
./login.sh

# Windows
login.bat
```
This will open a browser where you login with Google, then automatically save your SACSID.

**Option B: Manual SACSID**
Get your SACSID cookie from https://mtgarena.appspot.com:
- Open DevTools (F12) → Application → Cookies
- Copy the SACSID value

```bash
# Linux/Mac
./update_sacsid.sh YOUR_SACSID_HERE

# Windows
update_sacsid.bat YOUR_SACSID_HERE
```

### 3. Process a Tournament

**Interactive Mode:**
```bash
# Linux/Mac
./process_tournament.sh

# Windows
process_tournament.bat
```

**Command Line:**
```bash
# Linux/Mac
./process_tournament.sh <tournament_url_or_id> <encoded_id> --update-sheets

# Windows
process_tournament.bat <tournament_url_or_id> <encoded_id> --update-sheets
```

**Supported URL Formats:**
- Full URL: `https://mtgarena.appspot.com/#t4651297216135168`
- Hash format: `#t4651297216135168`
- Short format: `t4651297216135168`
- Numeric ID: `4651297216135168`

## Usage Examples

### Basic Processing (Dry-run)
```bash
# Using full URL (easy copy-paste from browser)
./process_tournament.sh https://mtgarena.appspot.com/#t4651297216135168 QhlSGUAAA

# Using numeric ID
./process_tournament.sh 4651297216135168 QhlSGUAAA
```

### Update Google Sheets
```bash
./process_tournament.sh https://mtgarena.appspot.com/#t4651297216135168 QhlSGUAAA --update-sheets
```

### Champion Event (2× Points)
```bash
./process_tournament.sh #t4651297216135168 QhlSGUAAA --update-sheets --champion
```

## Getting the Encoded Tournament ID

The MTGA API requires a GWT-encoded tournament ID. To get it:

1. Visit the tournament page in your browser
2. Open DevTools (F12) → Network tab
3. Find the POST request to `/arena/tournament`
4. Click Payload tab
5. Copy the value before the last `|` (e.g., `QhlSGUAAA`)

## Output

The script provides human-readable tournament results:

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
...

Prize Pool Increment: +100 NIS
======================================================================
```

## League Scoring Rules

- **All players**: +1 participation point
- **1st place**: +4 bonus points (total: 5)
- **2nd place**: +3 bonus points (total: 4)
- **3rd-4th**: +1-2 bonus points (based on player count)
- **5th-8th**: +1 bonus point (if 21+ players)
- **Champion events**: All points doubled
- **Prize pool**: 5 NIS per player

## Google Sheets Setup (Optional)

To enable automatic sheets updates, choose one option:

### Option A: OAuth (Easier - Recommended)

1. **Create OAuth credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create project → Enable Google Sheets API
   - Create OAuth 2.0 Client ID (Desktop app)
   - Download as `client_secret.json`

2. **Run setup:**
   ```bash
   ./venv/bin/python3 setup_google_sheets.py
   ```
   This opens a browser for authorization and saves credentials.

3. **Configure `.env`:**
   ```
   SPREADSHEET_KEY=your_spreadsheet_key_here
   ```

### Option B: Service Account (Advanced)

1. Create Service Account in Google Cloud Console
2. Download JSON as `service_account.json`
3. Share your Sheet with the service account email
4. Configure `.env` as above

## Project Structure

```
TopDeckProject/
├── process_tournament_complete.py  # Main processor script
├── process_tournament.sh           # Linux/Mac wrapper
├── process_tournament.bat          # Windows wrapper
├── fetch_tournament_simple.py      # Standalone fetcher
├── parse_tournament_url.py         # URL/ID parser
├── google_login.py                 # Automated SACSID extraction
├── setup_google_sheets.py          # OAuth setup for Sheets
├── login.sh / login.bat            # Google login wrappers
├── update_sacsid.sh / .bat         # Cookie updater
├── test_tournament.sh              # Test script
├── mtga_fetch.py                   # GWT-RPC utilities
├── league_logic.py                 # Points calculation
├── sheets_io.py                    # Google Sheets I/O
├── name_match.py                   # Fuzzy name matching
├── app.py                          # FastAPI server (optional)
├── requirements.txt                # Python dependencies
├── QUICK_START_GUIDE.md            # Quick reference
├── WINDOWS_GUIDE.md                # Windows-specific guide
└── SOLUTION_SUMMARY.md             # Technical documentation
```

## Windows Users

See [WINDOWS_GUIDE.md](WINDOWS_GUIDE.md) for detailed Windows-specific instructions, including:
- Python installation
- Virtual environment setup
- Batch file usage
- Troubleshooting

## FastAPI Server (Optional)

The project includes an optional REST API for automation:

```bash
# Linux/Mac
./start_server.sh

# Windows
start_server.bat
```

API will be available at:
- http://127.0.0.1:8000
- Interactive docs: http://127.0.0.1:8000/docs

### Key Endpoints:
- `POST /auth/set-sacsid` - Store SACSID cookie
- `GET /auth/status` - Check authentication
- `POST /api/league/update-from-url` - Process tournament from URL
- `POST /api/league/update` - Process with manual standings

## Troubleshooting

**"SACSID cookie is missing"**
→ Run `./update_sacsid.sh YOUR_SACSID` first

**"Failed to fetch tournament"**
→ SACSID may be expired - get a fresh one from your browser

**"No module named 'gspread'"**
→ Make sure you've activated the virtual environment and installed dependencies

**"HTTP 500 error"**
→ Check that you're logged into mtgarena.appspot.com

## Technical Details

- **Protocol**: GWT-RPC (Google Web Toolkit Remote Procedure Call)
- **Authentication**: SACSID session cookie
- **Data Format**: Custom GWT serialization
- **Encoding**: Tournament IDs use GWT's proprietary base64 encoding
- **Parsing**: Regex-based extraction from GWT-RPC response

## Limitations

- Encoded tournament ID must be manually extracted from browser DevTools
- SACSID cookies expire after ~24 hours and must be refreshed
- Google OAuth login may have different permissions than classic auth
- Final standings must match the order players finished

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details

## Support

For issues or questions:
- Check [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) for usage help
- See [WINDOWS_GUIDE.md](WINDOWS_GUIDE.md) for Windows-specific issues
- Review [SOLUTION_SUMMARY.md](SOLUTION_SUMMARY.md) for technical details
- Open an issue on GitHub

## Credits

Built for TopDeck League management system.
