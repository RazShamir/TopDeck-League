import json
import os
from typing import Optional

_STORE_FILE = ".sacsid.json"


def _read_store() -> dict:
    if not os.path.exists(_STORE_FILE):
        return {}
    try:
        with open(_STORE_FILE, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}


def _write_store(data: dict) -> None:
    tmp = _STORE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, _STORE_FILE)


def set_sacsid_stored(token: str) -> None:
    data = _read_store()
    data["sacsid"] = token
    _write_store(data)


def get_sacsid_stored() -> Optional[str]:
    data = _read_store()
    tok = data.get("sacsid")
    if tok and isinstance(tok, str):
        return tok
    return None


def clear_sacsid_stored() -> None:
    if os.path.exists(_STORE_FILE):
        try:
            os.remove(_STORE_FILE)
        except Exception:
            pass

