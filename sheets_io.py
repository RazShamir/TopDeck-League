"""Google Sheets I/O helpers (Hebrew-friendly + auto-find + idempotency)."""

import gspread
from google.oauth2.service_account import Credentials
from google.oauth2.credentials import Credentials as OAuthCredentials
import pickle
import os
from typing import Dict, List, Tuple

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS_FILE = "service_account.json"

# ---- Header labels (English by default; Hebrew can be added explicitly) ----
# We normalize header text to lowercase when matching.
PLAYER_HEADERS = {"player", "players", "player_name", "name"}
POINTS_HEADERS = {"points", "score", "scores", "total points", "total_points"}
PRIZE_LABELS = {"prize pool"}

DEFAULT_PLAYER_HEADER = "Player"
DEFAULT_POINTS_HEADER = "Points"
DEFAULT_PRIZE_HEADER = "Prize Pool"

# History headers (use English for now to avoid mojibake)
HISTORY_HEADERS_EN = [
    "Timestamp",
    "TournamentID",
    "IsLeague",
    "IsChampion",
    "Participants",
    "PrizeAddedNIS",
    "Top8CSV",
    "Note",
]
HISTORY_HEADERS_HE = HISTORY_HEADERS_EN


def _client_and_sheet(spreadsheet_key: str):
    # Try OAuth credentials first (easier setup)
    if os.path.exists('token.pickle'):
        try:
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
            gc = gspread.authorize(creds)
            sh = gc.open_by_key(spreadsheet_key)
            return gc, sh
        except Exception as e:
            print(f"Warning: Could not use OAuth credentials: {e}")

    # Fall back to service account
    if os.path.exists(CREDS_FILE):
        creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(spreadsheet_key)
        return gc, sh

    raise FileNotFoundError(
        "No Google credentials found. Please run:\n"
        "  ./venv/bin/python3 setup_google_sheets.py  (for OAuth)\n"
        "  OR place service_account.json in project root"
    )


def open_ws(spreadsheet_key: str, worksheet_name: str):
    _, sh = _client_and_sheet(spreadsheet_key)
    try:
        return sh.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        return sh.add_worksheet(title=worksheet_name, rows=1000, cols=26)


def auto_find_players_ws(spreadsheet_key: str):
    """Find the first worksheet whose header includes both Player and Points (case-insensitive)."""
    _, sh = _client_and_sheet(spreadsheet_key)
    for ws in sh.worksheets():
        vals = ws.get_all_values()
        if not vals or not vals[0]:
            continue
        header_lc = [c.strip().lower() for c in vals[0]]
        has_name = any(h in PLAYER_HEADERS for h in header_lc)
        has_pts = any(h in POINTS_HEADERS for h in header_lc)
        if has_name and has_pts:
            return ws
    raise ValueError(
        "Could not auto-detect a Players worksheet. Ensure a tab has a header row"
        " with both a Player column and a Points column."
    )


def _find_header_indices(header_row: List[str]) -> Tuple[int, int]:
    name_idx = points_idx = None
    for i, cell in enumerate(header_row):
        t = (cell or "").strip().lower()
        if t in PLAYER_HEADERS and name_idx is None:
            name_idx = i
        if t in POINTS_HEADERS and points_idx is None:
            points_idx = i
    if name_idx is None or points_idx is None:
        raise ValueError("Header row must include both a Player and Points column.")
    return name_idx, points_idx


def ensure_players_header(ws):
    vals = ws.get_all_values()
    if not vals:
        ws.update("A1:B1", [[DEFAULT_PLAYER_HEADER, DEFAULT_POINTS_HEADER]])
    else:
        # Check if first row has proper headers
        header_row = vals[0] if vals else []
        header_lc = [c.strip().lower() for c in header_row]
        has_name = any(h in PLAYER_HEADERS for h in header_lc)
        has_pts = any(h in POINTS_HEADERS for h in header_lc)

        # If headers are missing, update them
        if not (has_name and has_pts):
            ws.update("A1:B1", [[DEFAULT_PLAYER_HEADER, DEFAULT_POINTS_HEADER]])


def ensure_summary(ws):
    vals = ws.get_all_values()
    if not vals:
        ws.update("A1:B1", [[DEFAULT_PRIZE_HEADER, "0"]])
    else:
        # If B1 is empty, set it to 0 (use list-of-lists form)
        if not ws.acell("B1").value:
            ws.update("B1", [["0"]])


def read_existing_table(ws):
    data = ws.get_all_values()
    if not data:
        data = [[DEFAULT_PLAYER_HEADER, DEFAULT_POINTS_HEADER]]
        ws.update("A1:B1", data[0])
    name_idx, points_idx = _find_header_indices(data[0])
    return data, name_idx, points_idx


def upsert_points(ws, points: Dict[str, int], resolve_name):
    data, name_idx, points_idx = read_existing_table(ws)

    idx_by_name: Dict[str, int] = {}
    for r_i, row in enumerate(data[1:], start=2):
        if len(row) <= name_idx:
            continue
        nm = (row[name_idx] or "").strip()
        if nm:
            idx_by_name[nm] = r_i
    existing_names = list(idx_by_name.keys())

    for raw, delta in points.items():
        resolved, is_new = resolve_name(raw, existing_names)
        if is_new:
            width_needed = max(name_idx, points_idx) + 1
            new_row = ["" for _ in range(width_needed)]
            new_row[name_idx] = resolved
            new_row[points_idx] = str(delta)
            data.append(new_row)
            idx_by_name[resolved] = len(data)
            existing_names.append(resolved)
        else:
            r = idx_by_name[resolved]
            while len(data) < r:
                data.append([])
            row = data[r - 1]
            while len(row) <= points_idx:
                row.append("")
            try:
                cur = int((row[points_idx] or "0").strip())
            except ValueError:
                cur = 0
            row[points_idx] = str(cur + delta)

    ws.update("A1", data)


def update_prize_pool(ws_summary, increment_nis: int):
    header = (ws_summary.acell("A1").value or "").strip().lower()
    if header not in PRIZE_LABELS:
        ws_summary.update("A1:B1", [[DEFAULT_PRIZE_HEADER, "0"]])

    current_val = ws_summary.acell("B1").value or "0"
    try:
        cur = int(current_val)
    except ValueError:
        cur = 0

    ws_summary.update("B1", [[str(cur + increment_nis)]])


def ensure_history(ws, hebrew: bool = True):
    vals = ws.get_all_values()
    if not vals:
        ws.update("A1:H1", [HISTORY_HEADERS_HE if hebrew else HISTORY_HEADERS_EN])


def append_history(ws, row: list):
    ws.append_row(row, value_input_option="RAW")


# --- Idempotency helpers (column 2 = TournamentID) ---
def history_has_tournament(ws, tournament_id: str) -> bool:
    vals = ws.col_values(2)  # column B
    return tournament_id in set(vals[1:])  # skip header


def append_history_row(ws, row: list):
    ws.append_row(row, value_input_option="RAW")
