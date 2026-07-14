"""Sync jobs pulling FPL data into the local database."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data_sources import fpl
from app.models import Gameweek, League, Player, PlayerStatsWeekly


def get_or_create_premier_league(db: Session) -> League:
    league = db.scalar(select(League).where(League.code == "PL"))
    if league is None:
        league = League(code="PL", name="Premier League", is_active=True)
        db.add(league)
        db.flush()
    return league


def sync_players(db: Session) -> dict:
    """Upsert all PL players from FPL bootstrap, keyed by fpl_id."""
    data = fpl.fetch_bootstrap()
    league = get_or_create_premier_league(db)

    teams = {t["id"]: t["name"] for t in data.get("teams", [])}
    elements = data.get("elements", [])

    existing = {
        p.fpl_id: p
        for p in db.scalars(select(Player).where(Player.league_id == league.id))
        if p.fpl_id is not None
    }

    created, updated = 0, 0
    for el in elements:
        fields = {
            "name": el.get("web_name") or f"{el.get('first_name', '')} {el.get('second_name', '')}".strip(),
            "club": teams.get(el.get("team"), "Unknown"),
            "position": fpl.POSITION_MAP.get(el.get("element_type"), "MID"),
            "status": fpl.STATUS_MAP.get(el.get("status"), "available"),
            "price": (el.get("now_cost") or 0) / 10,
            "total_points": el.get("total_points") or 0,
        }
        player = existing.get(el["id"])
        if player is None:
            db.add(Player(league_id=league.id, fpl_id=el["id"], **fields))
            created += 1
        else:
            for key, value in fields.items():
                setattr(player, key, value)
            updated += 1

    db.commit()
    return {"created": created, "updated": updated, "total_elements": len(elements)}


def sync_gameweeks(db: Session) -> dict:
    """Upsert the gameweek schedule (deadlines, finished flags) from FPL bootstrap events."""
    from datetime import datetime

    data = fpl.fetch_bootstrap()
    league = get_or_create_premier_league(db)
    events = data.get("events", [])

    existing = {
        gw.number: gw
        for gw in db.scalars(select(Gameweek).where(Gameweek.league_id == league.id))
    }
    upserted = 0
    for ev in events:
        deadline = None
        if ev.get("deadline_time"):
            deadline = datetime.fromisoformat(ev["deadline_time"].replace("Z", "+00:00"))
        gw = existing.get(ev["id"])
        if gw is None:
            db.add(Gameweek(league_id=league.id, number=ev["id"], deadline=deadline,
                            finished=ev.get("finished", False)))
        else:
            gw.deadline = deadline
            gw.finished = ev.get("finished", False)
        upserted += 1
    db.commit()
    return {"gameweeks": upserted}


def sync_gameweek(db: Session, gameweek: int) -> dict:
    """Upsert weekly stats for one gameweek from the FPL live endpoint."""
    data = fpl.fetch_gameweek_live(gameweek)
    elements = data.get("elements", [])
    if not elements:
        return {"gameweek": gameweek, "synced": 0, "message": "No live data for this gameweek (FPL may be between seasons)."}

    players_by_fpl_id = {
        p.fpl_id: p for p in db.scalars(select(Player).where(Player.fpl_id.is_not(None)))
    }
    existing_stats = {
        s.player_id: s
        for s in db.scalars(select(PlayerStatsWeekly).where(PlayerStatsWeekly.gameweek == gameweek))
    }

    synced, skipped = 0, 0
    for el in elements:
        player = players_by_fpl_id.get(el["id"])
        if player is None:
            skipped += 1
            continue
        s = el.get("stats", {})
        fields = {
            "minutes": s.get("minutes", 0),
            "goals": s.get("goals_scored", 0),
            "assists": s.get("assists", 0),
            "clean_sheets": s.get("clean_sheets", 0),
            "goals_conceded": s.get("goals_conceded", 0),
            "yellow_cards": s.get("yellow_cards", 0),
            "red_cards": s.get("red_cards", 0),
            "saves": s.get("saves", 0),
            "own_goals": s.get("own_goals", 0),
            "penalties_missed": s.get("penalties_missed", 0),
            "penalties_saved": s.get("penalties_saved", 0),
            "bonus": s.get("bonus", 0),
            "total_points": s.get("total_points", 0),
            "xg": _to_float(s.get("expected_goals")),
            "xa": _to_float(s.get("expected_assists")),
        }
        row = existing_stats.get(player.id)
        if row is None:
            db.add(PlayerStatsWeekly(player_id=player.id, gameweek=gameweek, **fields))
        else:
            for key, value in fields.items():
                setattr(row, key, value)
        synced += 1

    db.commit()
    return {"gameweek": gameweek, "synced": synced, "skipped_unknown_players": skipped}


def _to_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
