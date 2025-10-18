# placements_input.py
from rapidfuzz import process, fuzz

def resolve_placements_from_paste(pasted_text: str, roster: list[str], cutoff: int = 92) -> list[str]:
    """
    Turn a pasted standings list (one name per line, top = 1st) into a clean placements list,
    matching each pasted line to the closest name in the roster (Hebrew-safe).
    """
    lines = [ln.strip() for ln in pasted_text.splitlines() if ln.strip()]
    placements: list[str] = []
    for ln in lines:
        best = process.extractOne(ln, roster, scorer=fuzz.WRatio, score_cutoff=cutoff)
        placements.append(best[0] if best else ln)  # keep original if no good match
    return placements
