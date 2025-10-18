"""TopDeck League API

Manual standings + auto-find players tab + idempotency + URL fetch with SACSID header.
"""

import os
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from history import now_iso, top8_csv
from league_logic import calculate_points, prize_pool_increment
from mtga_fetch import fetch_and_parse, fetch_raw_only
from name_match import match_or_new
from placements_input import resolve_placements_from_paste
from sheets_io import (
    open_ws, ensure_summary, update_prize_pool,
    ensure_history, append_history,
    auto_find_players_ws, history_has_tournament, append_history_row,
)
from session_store import get_sacsid_stored, set_sacsid_stored, clear_sacsid_stored

load_dotenv()

# --- env config ---
SPREADSHEET_KEY = os.getenv("SPREADSHEET_KEY", "")
# Clean, ASCII-safe defaults; override in .env if desired
SUMMARY_TAB = os.getenv("SUMMARY_TAB", "Summary")
HISTORY_TAB = os.getenv("HISTORY_TAB", "History")
API_TOKEN = os.getenv("API_TOKEN", "")

if not SPREADSHEET_KEY:
    raise RuntimeError("SPREADSHEET_KEY missing in .env")

app = FastAPI(title="TopDeck League API", version="1.3.0")


def require_token(x_api_token: Optional[str] = Header(None)):
    if not API_TOKEN:
        return  # not recommended, but allowed for local dev
    if x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Token")


# -------------------- Models --------------------


class ManualUpdateRequest(BaseModel):
    roster: List[str] = Field(
        ..., description="Full list of players who participated (Hebrew-safe)."
    )
    standings_text: str = Field(
        ..., description="Final standings paste, one name per line, 1st at top."
    )
    is_champion: bool = False
    is_league: bool = True
    spreadsheet_key: Optional[str] = None
    tournament_id: Optional[str] = None
    dry_run: bool = False


class UrlUpdateRequest(BaseModel):
    tournament_url_or_id: str
    is_champion: bool = False
    is_league: bool = True
    spreadsheet_key: Optional[str] = None
    # Fallbacks if not provided via headers
    sacsid: Optional[str] = None
    gwt_permutation: Optional[str] = None
    strong_name: Optional[str] = None
    dry_run: bool = False
    require_title_contains: Optional[str] = "Topdeck League"


# -------------------- Endpoints --------------------


@app.get("/health")
def health():
    return {"ok": True, "time": now_iso()}


@app.get("/debug/players-from-url")
def debug_players_from_url(
    tournament_url_or_id: str,
    x_api_token: Optional[str] = Header(None),
    x_sacsid: Optional[str] = Header(None),
    gwt_permutation: Optional[str] = None,
    strong_name: Optional[str] = None,
):
    require_token(x_api_token)
    sacsid = (x_sacsid or get_sacsid_stored() or "").strip()
    if not sacsid:
        return JSONResponse(
            status_code=400, content={"ok": False, "error": "Missing X-SACSID header"}
        )
    try:
        players, final_order = fetch_and_parse(
            tournament_url_or_id,
            sacsid=sacsid,
            strong_name=(strong_name or "").strip(),
            gwt_permutation=(gwt_permutation or "").strip(),
        )
        return {
            "ok": True,
            "participants": len(players),
            "players_detected": players,
            "final_order_inferred": bool(final_order),
        }
    except Exception as e:
        return JSONResponse(status_code=400, content={"ok": False, "error": str(e)})


@app.get("/debug/fetch-raw")
def debug_fetch_raw(
    tournament_url_or_id: str,
    x_api_token: Optional[str] = Header(None),
    x_sacsid: Optional[str] = Header(None),
    gwt_permutation: Optional[str] = None,
    strong_name: Optional[str] = None,
):
    require_token(x_api_token)
    sacsid = (x_sacsid or get_sacsid_stored() or "").strip()
    if not sacsid:
        return JSONResponse(
            status_code=400, content={"ok": False, "error": "Missing X-SACSID header"}
        )
    try:
        raw = fetch_raw_only(
            tournament_url_or_id,
            sacsid=sacsid,
            strong_name=(strong_name or "").strip(),
            gwt_permutation=(gwt_permutation or "").strip(),
        )
        # Return trimmed preview + full raw (string)
        return {
            "ok": True,
            "preview": raw[:500] + ("..." if len(raw) > 500 else ""),
            "raw": raw,
        }
    except Exception as e:
        return JSONResponse(status_code=400, content={"ok": False, "error": str(e)})


@app.get("/debug/detect-players")
def debug_detect_players(x_api_token: Optional[str] = Header(None)):
    require_token(x_api_token)
    ws = auto_find_players_ws(SPREADSHEET_KEY)
    headers = ws.row_values(1)
    return {"worksheet_title": ws.title, "header_row_1": headers}


@app.post("/api/league/update")
def update_league(req: ManualUpdateRequest, x_api_token: Optional[str] = Header(None)):
    require_token(x_api_token)
    try:
        sheet_key = req.spreadsheet_key or SPREADSHEET_KEY
        placements = resolve_placements_from_paste(
            req.standings_text, req.roster, cutoff=92
        )
        participants = len(req.roster)

        points = calculate_points(
            placements, participants, is_champion=req.is_champion
        )
        pool_add = prize_pool_increment(participants)

        # If dry_run, do not write to sheets; return preview only
        if req.dry_run or not req.is_league:
            return {
                "ok": True,
                "participants": participants,
                "placements_top8": placements[:8],
                "points_preview_first10": list(points.items())[:10],
                "prize_pool_add": pool_add,
                "wrote_to_sheet": False,
                "dry_run": True,
            }

        ws_players = auto_find_players_ws(sheet_key)
        ws_summary = open_ws(sheet_key, SUMMARY_TAB)
        ensure_summary(ws_summary)
        ws_history = open_ws(sheet_key, HISTORY_TAB)
        ensure_history(ws_history, hebrew=True)

        tid = req.tournament_id or ("manual-" + now_iso())
        if (
            req.is_league
            and req.tournament_id
            and history_has_tournament(ws_history, req.tournament_id)
        ):
            return {
                "ok": True,
                "skipped": True,
                "reason": "Tournament already logged",
                "tournament_id": req.tournament_id,
            }

        wrote = False
        if req.is_league:
            from sheets_io import upsert_points

            upsert_points(
                ws_players,
                points,
                lambda n, exist: match_or_new(n, exist, score_cutoff=92),
            )
            update_prize_pool(ws_summary, pool_add)
            append_history_row(
                ws_history,
                [
                    now_iso(),
                    tid,
                    str(req.is_league),
                    str(req.is_champion),
                    str(participants),
                    str(pool_add),
                    top8_csv(placements),
                    "",
                ],
            )
            wrote = True

        return {
            "ok": True,
            "participants": participants,
            "placements_top8": placements[:8],
            "points_preview_first10": list(points.items())[:10],
            "prize_pool_add": pool_add,
            "wrote_to_sheet": wrote,
            "tournament_id": tid,
        }

    except Exception as e:
        return JSONResponse(status_code=400, content={"ok": False, "error": str(e)})


@app.post("/api/league/update-from-url")
def update_from_url(
    req: UrlUpdateRequest,
    x_api_token: Optional[str] = Header(None),
    x_sacsid: Optional[str] = Header(None),  # header support
):
    require_token(x_api_token)
    try:
        sheet_key = req.spreadsheet_key or SPREADSHEET_KEY

        # Prefer SACSID from header, fallback to body
        sacsid_value = (x_sacsid or req.sacsid or get_sacsid_stored() or "").strip()
        if not sacsid_value:
            raise ValueError("Missing SACSID. Provide it in header X-SACSID.")

        # Fetch raw first to validate tournament title if needed
        raw_preview = fetch_raw_only(
            req.tournament_url_or_id,
            sacsid=sacsid_value,
            strong_name=(req.strong_name or "").strip(),
            gwt_permutation=(req.gwt_permutation or "").strip(),
        )
        marker = (req.require_title_contains or "").strip()
        if req.is_league and marker and marker.lower() not in raw_preview.lower():
            return JSONResponse(status_code=400, content={
                "ok": False,
                "error": f"Tournament does not appear to be '{marker}'.",
                "hint": "Adjust require_title_contains or set is_league=false to skip writing."
            })

        # Fetch & parse from site
        players, final_order = fetch_and_parse(
            req.tournament_url_or_id,
            sacsid=sacsid_value,
            strong_name=(req.strong_name or "").strip(),
            gwt_permutation=(req.gwt_permutation or "").strip(),
        )
        participants = len(players)

        if not final_order:
            return {
                "ok": True,
                "participants": participants,
                "players_detected": players,
                "final_order_inferred": False,
                "hint": "Parser couldn't infer final order yet. Copy 'standings_text' into /api/league/update.",
                "standings_text": "\n".join(players),
            }

        placements = final_order
        points = calculate_points(placements, participants, is_champion=req.is_champion)
        pool_add = prize_pool_increment(participants)

        # If dry_run or non-league, do not write; return preview only
        if req.dry_run or not req.is_league:
            return {
                "ok": True,
                "participants": participants,
                "placements_top8": placements[:8],
                "prize_pool_add": pool_add,
                "wrote_to_sheet": False,
                "dry_run": True,
            }

        ws_players = auto_find_players_ws(sheet_key)
        ws_summary = open_ws(sheet_key, SUMMARY_TAB)
        ensure_summary(ws_summary)
        ws_history = open_ws(sheet_key, HISTORY_TAB)
        ensure_history(ws_history, hebrew=True)

        tid = "url-" + req.tournament_url_or_id.strip().split("#t")[-1]
        if req.is_league and history_has_tournament(ws_history, tid):
            return {
                "ok": True,
                "skipped": True,
                "reason": "Tournament already logged",
                "tournament_id": tid,
            }

        from sheets_io import upsert_points

        upsert_points(
            ws_players, points, lambda n, exist: match_or_new(n, exist, score_cutoff=92)
        )
        update_prize_pool(ws_summary, pool_add)
        append_history_row(
            ws_history,
            [now_iso(), tid, str(req.is_league), str(req.is_champion), str(participants), str(pool_add), top8_csv(placements), ""],
        )

        return {
            "ok": True,
            "participants": participants,
            "placements_top8": placements[:8],
            "prize_pool_add": pool_add,
            "wrote_to_sheet": True,
            "tournament_id": tid,
        }

    except Exception as e:
        return JSONResponse(status_code=400, content={"ok": False, "error": str(e)})


# -------------------- Auth / Session Endpoints --------------------

class SetSACSIDRequest(BaseModel):
    sacsid: Optional[str] = None


@app.post("/auth/set-sacsid")
def auth_set_sacsid(
    body: SetSACSIDRequest,
    x_api_token: Optional[str] = Header(None),
    x_sacsid: Optional[str] = Header(None),
):
    require_token(x_api_token)
    token = (x_sacsid or (body.sacsid if body else None) or "").strip()
    if not token:
        return JSONResponse(status_code=400, content={"ok": False, "error": "Missing SACSID"})
    set_sacsid_stored(token)
    masked = token[:4] + "..." + token[-4:]
    return {"ok": True, "stored": True, "sacsid_masked": masked}


@app.get("/auth/status")
def auth_status(
    x_api_token: Optional[str] = Header(None),
    tournament_url_or_id: Optional[str] = Query(None),
):
    require_token(x_api_token)
    token = get_sacsid_stored()
    if not token:
        return {"ok": True, "stored": False}
    resp = {"ok": True, "stored": True, "sacsid_masked": token[:4] + "..." + token[-4:]}
    if tournament_url_or_id:
        try:
            raw = fetch_raw_only(tournament_url_or_id, sacsid=token)
            resp.update({"probe_ok": True, "preview": raw[:80]})
        except Exception as e:
            resp.update({"probe_ok": False, "error": str(e)})
    return resp


@app.post("/auth/clear")
def auth_clear(
    x_api_token: Optional[str] = Header(None),
):
    require_token(x_api_token)
    clear_sacsid_stored()
    return {"ok": True, "cleared": True}
