# TopDeck Project File Structure

## Core Files

### Main Scripts
- **process_tournament_complete.py** - Main tournament processor with interactive mode
- **process_tournament.sh** - Linux/Mac wrapper script
- **process_tournament.bat** - Windows wrapper script

### Utilities
- **fetch_tournament_simple.py** - Standalone tournament fetcher (no sheets update)
- **update_sacsid.sh / .bat** - SACSID cookie management
- **extract_from_curl.sh** - Extract encoded ID from curl command
- **test_tournament.sh** - Test script for validation

### Python Modules
- **app.py** - FastAPI REST API server (optional)
- **mtga_fetch.py** - GWT-RPC protocol handlers
- **league_logic.py** - Points and prize pool calculation
- **sheets_io.py** - Google Sheets integration
- **name_match.py** - Fuzzy name matching for player names
- **history.py** - Tournament history utilities
- **session_store.py** - SACSID session management
- **placements_input.py** - Manual placement input handlers

### Server Scripts
- **start_server.sh** - Start FastAPI server (Linux/Mac)
- **start_server.bat** - Start FastAPI server (Windows)

### Test Scripts
- **run_tests.sh** - Run test suite (Linux/Mac)
- **run_tests.bat** - Run test suite (Windows)
- **scripts/smoke_url_fetch.py** - Smoke test for URL fetching

## Documentation

### User Guides
- **README.md** - Main GitHub README with quick start
- **QUICK_START_GUIDE.md** - Step-by-step usage guide
- **WINDOWS_GUIDE.md** - Windows-specific instructions

### Technical Documentation
- **SOLUTION_SUMMARY.md** - Complete technical overview and design decisions

## Configuration Files

- **requirements.txt** - Python dependencies
- **.env** - Environment variables (spreadsheet keys, tokens)
- **.sacsid.json** - Stored SACSID cookie (auto-generated)
- **service_account.json** - Google Service Account credentials (user-provided)

## Data Files

- **tournament_*_data.txt** - Cached tournament data (auto-generated)

## Removed Files

The following obsolete files have been removed:
- QUICKSTART.md (replaced by QUICK_START_GUIDE.md)
- PROJECT_PLAN.md (obsolete planning doc)
- STATUS.md (obsolete status tracking)
- FIXES_APPLIED.md (obsolete bug tracking)
- COOKIE_SOLUTIONS.md (obsolete workaround doc)
- BROWSER_CONSOLE_SCRIPT.md (obsolete extraction method)
- REAL_WORLD_TEST_CHECKLIST.md (obsolete testing doc)
- TESTING_GUIDE.md (replaced by test_tournament.sh)
- WINDOWS_SETUP.md (replaced by WINDOWS_GUIDE.md)
- process_tournament.py (replaced by process_tournament_complete.py)
- auto_fetch_tournament.py (obsolete automation attempt)
- capture_encoded_id.py (obsolete extraction script)
- run_demo.py (obsolete demo script)
- run_manual.py (obsolete manual script)
- run_to_sheet.py (integrated into main script)
- test_direct_fetch.py (replaced by integrated tests)
- parser_test.py (replaced by integrated tests)
- test_fetch_raw.sh (replaced by test_tournament.sh)
- test_with_browser_payload.sh (replaced by test_tournament.sh)
- sample_response.txt (obsolete sample data)
