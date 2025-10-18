# history.py
from datetime import datetime, timezone

def now_iso():
    """return current time in iso format (local timezone)."""
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S%z")

def top8_csv(placements):
    """return the top 8 players joined into one csv string."""
    return ",".join(placements[:8])
