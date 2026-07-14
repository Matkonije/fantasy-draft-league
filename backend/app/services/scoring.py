"""Gameweek scoring: FPL points with auto-substitution and captaincy."""

import logging
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Draft,
    FantasyLeague,
    Player,
    PlayerStatsWeekly,
    Team,
    TeamGameweekScore,
)
from app.services.lineup import STARTER_LIMITS, LineupError, ensure_lineup

logger = logging.getLogger(__name__)


def _formation_ok_after_swap(starter_positions: Counter, out_pos: str, in_pos: str) -> bool:
    counts = starter_positions.copy()
    counts[out_pos] -= 1
    counts[in_pos] += 1
    return all(lo <= counts[pos] <= hi for pos, (lo, hi) in STARTER_LIMITS.items())


def score_team_gameweek(db: Session, team: Team, gameweek: int) -> TeamGameweekScore:
    """Compute (and upsert) a team's score for one gameweek."""
    slots = ensure_lineup(db, team, gameweek)

    player_ids = [s.player_id for s in slots]
    players = {
        p.id: p for p in db.scalars(select(Player).where(Player.id.in_(player_ids)))
    }
    stats = {
        s.player_id: s
        for s in db.scalars(
            select(PlayerStatsWeekly).where(
                PlayerStatsWeekly.player_id.in_(player_ids),
                PlayerStatsWeekly.gameweek == gameweek,
            )
        )
    }

    def minutes(pid: int) -> int:
        return stats[pid].minutes if pid in stats else 0

    def points(pid: int) -> int:
        return stats[pid].total_points if pid in stats else 0

    starters = [s for s in slots if s.role == "starter"]
    bench = sorted((s for s in slots if s.role == "bench"), key=lambda s: s.bench_order)

    starter_positions = Counter(players[s.player_id].position for s in starters)
    final_xi: list[int] = [s.player_id for s in starters]
    subs: list[dict] = []
    used_bench: set[int] = set()

    for slot in starters:
        if minutes(slot.player_id) > 0:
            continue
        out_pos = players[slot.player_id].position
        for b in bench:
            if b.player_id in used_bench or minutes(b.player_id) == 0:
                continue
            in_pos = players[b.player_id].position
            # GK can only be replaced by GK; outfield swaps must keep the formation valid
            if (out_pos == "GK") != (in_pos == "GK"):
                continue
            if not _formation_ok_after_swap(starter_positions, out_pos, in_pos):
                continue
            final_xi.remove(slot.player_id)
            final_xi.append(b.player_id)
            used_bench.add(b.player_id)
            starter_positions[out_pos] -= 1
            starter_positions[in_pos] += 1
            subs.append({"out": slot.player_id, "in": b.player_id})
            break

    captain = next((s for s in starters if s.is_captain), None)
    vice = next((s for s in starters if s.is_vice), None)
    doubled_id = None
    if captain and minutes(captain.player_id) > 0:
        doubled_id = captain.player_id
    elif vice and minutes(vice.player_id) > 0:
        doubled_id = vice.player_id

    total = 0
    detail = []
    for pid in final_xi:
        pts = points(pid)
        multiplier = 2 if pid == doubled_id else 1
        total += pts * multiplier
        detail.append(
            {
                "player_id": pid,
                "name": players[pid].name,
                "position": players[pid].position,
                "points": pts,
                "multiplier": multiplier,
                "minutes": minutes(pid),
            }
        )

    breakdown = {"players": detail, "auto_subs": subs, "doubled_player_id": doubled_id}

    row = db.scalar(
        select(TeamGameweekScore).where(
            TeamGameweekScore.team_id == team.id, TeamGameweekScore.gameweek == gameweek
        )
    )
    if row is None:
        row = TeamGameweekScore(team_id=team.id, gameweek=gameweek)
        db.add(row)
    row.points = total
    row.breakdown = breakdown
    db.commit()
    db.refresh(row)
    return row


def compute_gameweek_scores(db: Session, league_id: int, gameweek: int) -> dict:
    """Score every team in every drafted fantasy league of this football league."""
    teams = db.scalars(
        select(Team)
        .join(FantasyLeague, FantasyLeague.id == Team.fantasy_league_id)
        .join(Draft, Draft.fantasy_league_id == FantasyLeague.id)
        .where(FantasyLeague.league_id == league_id, Draft.status == "completed")
        .distinct()
    ).all()

    scored, failed = 0, []
    for team in teams:
        try:
            score_team_gameweek(db, team, gameweek)
            scored += 1
        except LineupError as e:
            logger.warning("Cannot score team %s GW %s: %s", team.id, gameweek, e)
            failed.append({"team_id": team.id, "reason": str(e)})
    return {"gameweek": gameweek, "teams_scored": scored, "failed": failed}
