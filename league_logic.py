# league_logic.py
from typing import Dict, List

def calculate_points(
    placements: List[str],
    participants: int,
    is_champion: bool = False
) -> Dict[str, int]:
    """
    Everyone +1 participation.
    1st +4, 2nd +3.
    3rd–4th +1 (or +2 if participants >= 21).
    If participants >= 16: 5th–6th +1.
    If participants >= 21: 5th–8th +1 (and 3rd–4th +2 as above).
    Double all points if is_champion.
    """
    pts: Dict[str, int] = {}

    # +1 participation
    for name in placements[:participants]:
        pts[name] = pts.get(name, 0) + 1

    def add(place: int, val: int):
        idx = place - 1
        if 0 <= idx < len(placements):
            name = placements[idx]
            pts[name] = pts.get(name, 0) + val

    # podium
    add(1, 4)
    add(2, 3)

    if participants >= 21:
        add(3, 2); add(4, 2)
        for p in range(5, 9):
            add(p, 1)
    else:
        add(3, 1); add(4, 1)
        if participants >= 16:
            add(5, 1); add(6, 1)

    if is_champion:
        for k in list(pts.keys()):
            pts[k] *= 2

    return pts


def prize_pool_increment(participants: int, per_participant_nis: int = 5) -> int:
    return participants * per_participant_nis

