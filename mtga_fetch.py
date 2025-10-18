# mtga_fetch.py
import re
import json
import requests
from typing import List, Tuple, Optional

ARENA_BASE = "https://mtgarena.appspot.com"
TOURNAMENT_RPC = f"{ARENA_BASE}/arena/tournament"

# Defaults that worked for you earlier; can be overridden per-request
DEFAULT_GWT_MODULE_BASE = "https://mtgarena.appspot.com/arena/"
DEFAULT_GWT_PERMUTATION = "79B8599238A9627852278DC457BF90AA"
DEFAULT_STRONG_NAME = "F9916789951930449A4C1B88925C3ACF"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/138.0.0.0 Safari/537.36"
)

def extract_tournament_id(url_or_id: str) -> str:
    """
    Accepts:
      - full URL like https://mtgarena.appspot.com/#t5811915658887168
      - or just the numeric id: 5811915658887168
    Returns the numeric id as a string.
    """
    m = re.search(r"#t(\d+)", url_or_id)
    if m:
        return m.group(1)
    m2 = re.search(r"(\d{10,})", url_or_id)
    if m2:
        return m2.group(1)
    raise ValueError("Could not extract tournament id from input.")

def fetch_raw_only(
    url_or_id: str,
    sacsid: str,
    strong_name: str = DEFAULT_STRONG_NAME,
    gwt_permutation: str = DEFAULT_GWT_PERMUTATION
) -> str:
    tid = extract_tournament_id(url_or_id)
    return fetch_tournament_raw(tid, sacsid, strong_name=strong_name, gwt_permutation=gwt_permutation)

def build_gwt_payload(tournament_id: str, strong_name: str, encoded_id: str = None) -> str:
    """
    Build the GWT-RPC payload for TournamentService.getTournament(Long id).
    This shape matches the call you captured earlier.

    Args:
        tournament_id: The numeric tournament ID
        strong_name: GWT strong name
        encoded_id: Optional pre-encoded tournament ID (GWT base64 encoding)
                   If not provided, will use a fallback encoding
    """
    # Use provided encoded ID or try to encode it
    if not encoded_id:
        # Try to encode the tournament ID using GWT's encoding
        # This is a best-effort attempt
        import struct
        import base64
        try:
            # Convert tournament ID to bytes (little-endian 64-bit)
            tid_int = int(tournament_id)
            bytes_le = struct.pack('<Q', tid_int)
            # Encode to base64 and strip padding
            encoded_id = base64.b64encode(bytes_le).decode().rstrip('=')
        except:
            # Fallback to old value
            encoded_id = "UpegQUAAA"

    parts = [
        "7", "0", "5",
        DEFAULT_GWT_MODULE_BASE,
        strong_name,
        "com.snazzorama.arena.client.TournamentService",
        "getTournament",
        "java.lang.Long/4227064769",
        "1","2","3","4","1","5","5",encoded_id,""
    ]
    return "|".join(parts)

def fetch_tournament_raw(
    tournament_id: str,
    sacsid: str,
    strong_name: str = DEFAULT_STRONG_NAME,
    gwt_permutation: str = DEFAULT_GWT_PERMUTATION,
    timeout: int = 20
) -> str:
    """
    Calls the GWT endpoint with your SACSID cookie.
    Returns raw text like: //OK[ ... ]
    """
    # Match browser/Postman header casing exactly; include explicit Cookie header.
    headers = {
        "Accept": "*/*",
        "Content-Type": "text/x-gwt-rpc; charset=UTF-8",
        "Origin": ARENA_BASE,
        "Referer": f"{ARENA_BASE}/",
        "User-Agent": USER_AGENT,
        "X-GWT-Module-Base": DEFAULT_GWT_MODULE_BASE,
        "X-GWT-Permutation": gwt_permutation,
        "Cookie": f"SACSID={sacsid}",
    }
    # Also pass via requests cookies jar (harmless redundancy, some servers are picky)
    cookies = {"SACSID": sacsid}
    data = build_gwt_payload(tournament_id, strong_name)
    r = requests.post(TOURNAMENT_RPC, headers=headers, cookies=cookies, data=data, timeout=timeout)
    if r.status_code != 200:
        raise RuntimeError(f"RPC failed: HTTP {r.status_code} - {r.text[:200]}")
    if not r.text.startswith("//OK["):
        raise RuntimeError(f"Unexpected RPC body: {r.text[:200]}")
    return r.text

def _find_string_array_block(raw: str) -> str:
    # Find the first JSON-ish string array block inside the //OK[...] payload
    start = raw.find('["com.snazzorama.arena.client.Tournament')
    if start == -1:
        # fallback to first ["java.lang.String
        start = raw.find('["java.lang.String')
        if start == -1:
            raise ValueError("Could not find string array block.")
    # Count brackets to find matching closing ]
    depth = 0
    end = None
    for i in range(start, len(raw)):
        c = raw[i]
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                end = i
                break
    if end is None:
        raise ValueError("Unterminated string array block.")
    return raw[start:end+1]

def parse_players_from_rpc(raw: str) -> List[str]:
    """
    Extract player names (Hebrew-safe) from the string array block.
    We collect all strings after the 'java.lang.String/2004016611' marker
    until before the '[Lcom.snazzorama.arena.client.Tournament$RoundData;' marker.
    """
    block = _find_string_array_block(raw)
    arr = json.loads(block)
    try:
        s_idx = arr.index("java.lang.String/2004016611")
    except ValueError:
        # fallback: find first non-empty non-technical string after the known type list
        s_idx = 0
        for i, s in enumerate(arr):
            if isinstance(s, str) and s.startswith("java.lang.String/"):
                s_idx = i
                break
    names: List[str] = []
    for s in arr[s_idx+1:]:
        if not isinstance(s, str):
            continue
        if s.startswith("[Lcom.snazzorama.arena.client.Tournament$RoundData;"):
            break
        # heuristics: skip obvious non-names (emails, formats, empty)
        if not s.strip():
            continue
        if "@" in s and "." in s:
            continue
        names.append(s.strip())
    # De-dup while preserving order
    seen = set()
    uniq = []
    for n in names:
        if n not in seen:
            uniq.append(n)
            seen.add(n)
    return uniq

def try_parse_final_order(raw: str, players: List[str]) -> Optional[List[str]]:
    """
    Parse final standings from the RPC response using RoundData.

    The GWT-RPC response contains round data with match results and standings.
    We look for the final round's standings array to determine placement order.

    Returns ordered list of player names by placement, or None if parsing fails.
    """
    try:
        # Find the string array block containing tournament data
        block = _find_string_array_block(raw)
        arr = json.loads(block)

        # Look for round data marker
        round_marker = "[Lcom.snazzorama.arena.client.Tournament$RoundData;"

        # Find if we have round data in the response
        if round_marker not in arr:
            return None

        # Try to parse standings from the raw response
        # Look for numeric sequences that might represent standings/points
        # The approach: find player names order after the last round data

        # Alternative approach: look for standings table in raw text
        # Format often includes player records like "3-0", "2-1", etc.

        # Parse match records to infer standings
        standings_data = []

        # Search for patterns like: player_name followed by match record
        # This is heuristic-based since GWT-RPC format can vary

        for i, player in enumerate(players):
            # Try to find this player's final record in the raw data
            # Look for patterns like "3-0", "2-1", etc. near the player name
            player_pos = raw.find(f'"{player}"')
            if player_pos == -1:
                continue

            # Search nearby for match record pattern (W-L format)
            search_window = raw[max(0, player_pos-200):min(len(raw), player_pos+200)]

            # Look for win-loss record pattern
            import re
            records = re.findall(r'\b(\d+)-(\d+)\b', search_window)

            if records:
                # Take the first record found (most likely the match record)
                wins, losses = map(int, records[0])
                match_points = wins * 3  # Standard Magic scoring
                standings_data.append((player, wins, losses, match_points))

        # Sort by match points (descending), then by wins (descending)
        if standings_data:
            standings_data.sort(key=lambda x: (x[3], x[1]), reverse=True)
            ordered_players = [player for player, _, _, _ in standings_data]

            # Verify we got all players
            if len(ordered_players) == len(players):
                return ordered_players

        # If heuristic parsing failed, return None to fall back to manual entry
        return None

    except Exception:
        # If any parsing error occurs, fail gracefully
        return None

def fetch_and_parse(
    url_or_id: str,
    sacsid: str,
    strong_name: str = DEFAULT_STRONG_NAME,
    gwt_permutation: str = DEFAULT_GWT_PERMUTATION
) -> Tuple[List[str], Optional[List[str]]]:
    """
    Returns (players, final_order or None).
    """
    tid = extract_tournament_id(url_or_id)
    raw = fetch_tournament_raw(tid, sacsid, strong_name=strong_name, gwt_permutation=gwt_permutation)
    players = parse_players_from_rpc(raw)
    final_order = try_parse_final_order(raw, players)
    return players, final_order
