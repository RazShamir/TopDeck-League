from rapidfuzz import process, fuzz
from typing import List, Tuple

def normalize_name(s: str) -> str:
    # lightweight normalization; extend if you see recurring issues
    return s.strip()

def match_or_new(
    incoming_name: str,
    existing_names: List[str],
    score_cutoff: int = 90
) -> Tuple[str, bool]:
    """
    Returns (resolved_name, is_new).
    If a close match (>= score_cutoff) exists in existing_names, return that existing name.
    Otherwise return incoming_name and mark as new.
    """
    incoming = normalize_name(incoming_name)
    choices = [normalize_name(n) for n in existing_names]

    if not choices:
        return incoming, True

    best = process.extractOne(
        incoming, choices, scorer=fuzz.WRatio, score_cutoff=score_cutoff
    )
    if best:
        # find original-cased name by index
        idx = choices.index(best[0])
        return existing_names[idx], False
    return incoming, True
