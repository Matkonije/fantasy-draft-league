"""Client for the official Fantasy Premier League API."""

import httpx

BASE_URL = "https://fantasy.premierleague.com/api"

# FPL element_type -> our position codes
POSITION_MAP = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}

# FPL status flags: a=available, d=doubtful, i=injured, s=suspended, u=unavailable
STATUS_MAP = {
    "a": "available",
    "d": "doubtful",
    "i": "injured",
    "s": "suspended",
    "u": "unavailable",
    "n": "unavailable",
}

_HEADERS = {"User-Agent": "fantasy-draft-league/0.1"}


def fetch_bootstrap() -> dict:
    """Full FPL bootstrap: elements (players), teams, element_types, events."""
    with httpx.Client(headers=_HEADERS, timeout=30) as client:
        resp = client.get(f"{BASE_URL}/bootstrap-static/")
        resp.raise_for_status()
        return resp.json()


def fetch_gameweek_live(gameweek: int) -> dict:
    """Per-player stats for one gameweek."""
    with httpx.Client(headers=_HEADERS, timeout=30) as client:
        resp = client.get(f"{BASE_URL}/event/{gameweek}/live/")
        resp.raise_for_status()
        return resp.json()
