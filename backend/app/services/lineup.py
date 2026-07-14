"""Weekly lineup management: validation, defaults, deadline locking."""

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Draft, DraftPick, FantasyLeague, Gameweek, LineupSlot, Player, Team

# flexible FPL formations: exactly 1 GK, DEF 3-5, MID 2-5, FWD 1-3 in the starting XI
STARTER_LIMITS = {"GK": (1, 1), "DEF": (3, 5), "MID": (2, 5), "FWD": (1, 3)}
XI = 11


class LineupError(Exception):
    """Rule violation; message is safe to show to the user."""


def roster_players(db: Session, team: Team) -> dict[int, Player]:
    """Players owned by the team via its league's active/completed draft."""
    rows = db.scalars(
        select(Player)
        .join(DraftPick, DraftPick.player_id == Player.id)
        .join(Draft, Draft.id == DraftPick.draft_id)
        .where(
            DraftPick.team_id == team.id,
            Draft.fantasy_league_id == team.fantasy_league_id,
            Draft.status.in_(["active", "completed"]),
        )
    ).all()
    return {p.id: p for p in rows}


def formation_valid(positions: list[str]) -> bool:
    counts = {pos: positions.count(pos) for pos in STARTER_LIMITS}
    return len(positions) == XI and all(
        lo <= counts[pos] <= hi for pos, (lo, hi) in STARTER_LIMITS.items()
    )


def check_deadline(db: Session, team: Team, gameweek: int) -> None:
    fl = db.get(FantasyLeague, team.fantasy_league_id)
    gw = db.scalar(
        select(Gameweek).where(Gameweek.league_id == fl.league_id, Gameweek.number == gameweek)
    )
    # off-season fallback: with no synced schedule there is nothing to lock against
    if gw and gw.deadline and gw.deadline <= datetime.now(timezone.utc):
        raise LineupError(f"Deadline for gameweek {gameweek} has passed")


def set_lineup(
    db: Session,
    team: Team,
    gameweek: int,
    starter_ids: list[int],
    bench_ids: list[int],
    captain_id: int,
    vice_id: int,
    *,
    enforce_deadline: bool = True,
) -> list[LineupSlot]:
    if enforce_deadline:
        check_deadline(db, team, gameweek)

    roster = roster_players(db, team)
    if not roster:
        raise LineupError("Team has no drafted roster yet")

    all_ids = starter_ids + bench_ids
    if len(set(all_ids)) != len(all_ids):
        raise LineupError("Duplicate players in lineup")
    if set(all_ids) != set(roster):
        raise LineupError("Lineup must contain exactly the 15 drafted players")
    if len(starter_ids) != XI or len(bench_ids) != 4:
        raise LineupError("Lineup needs 11 starters and 4 bench players")

    if not formation_valid([roster[pid].position for pid in starter_ids]):
        raise LineupError("Invalid formation: need 1 GK, 3-5 DEF, 2-5 MID, 1-3 FWD")

    bench_positions = [roster[pid].position for pid in bench_ids]
    if bench_positions.count("GK") != 1:
        raise LineupError("Bench must contain exactly 1 GK")

    if captain_id not in starter_ids or vice_id not in starter_ids:
        raise LineupError("Captain and vice-captain must be starters")
    if captain_id == vice_id:
        raise LineupError("Captain and vice-captain must be different players")

    db.execute(delete(LineupSlot).where(LineupSlot.team_id == team.id, LineupSlot.gameweek == gameweek))

    slots = []
    for pid in starter_ids:
        slots.append(
            LineupSlot(
                team_id=team.id, gameweek=gameweek, player_id=pid, role="starter",
                is_captain=pid == captain_id, is_vice=pid == vice_id,
            )
        )
    # bench GK is always order 0; outfield keep the submitted order 1-3
    outfield_order = 1
    for pid in bench_ids:
        if roster[pid].position == "GK":
            order = 0
        else:
            order = outfield_order
            outfield_order += 1
        slots.append(
            LineupSlot(team_id=team.id, gameweek=gameweek, player_id=pid, role="bench", bench_order=order)
        )
    db.add_all(slots)
    db.commit()
    return slots


def get_lineup(db: Session, team_id: int, gameweek: int) -> list[LineupSlot]:
    return db.scalars(
        select(LineupSlot).where(LineupSlot.team_id == team_id, LineupSlot.gameweek == gameweek)
    ).all()


def ensure_lineup(db: Session, team: Team, gameweek: int) -> list[LineupSlot]:
    """Return the team's lineup for the GW, copying the previous GW or generating a default."""
    existing = get_lineup(db, team.id, gameweek)
    if existing:
        return existing

    previous = db.scalars(
        select(LineupSlot)
        .where(LineupSlot.team_id == team.id, LineupSlot.gameweek < gameweek)
        .order_by(LineupSlot.gameweek.desc())
    ).all()
    if previous:
        last_gw = previous[0].gameweek
        slots = [
            LineupSlot(
                team_id=team.id, gameweek=gameweek, player_id=s.player_id, role=s.role,
                bench_order=s.bench_order, is_captain=s.is_captain, is_vice=s.is_vice,
            )
            for s in previous
            if s.gameweek == last_gw
        ]
        db.add_all(slots)
        db.commit()
        return slots

    return generate_default_lineup(db, team, gameweek)


def generate_default_lineup(db: Session, team: Team, gameweek: int) -> list[LineupSlot]:
    """Best valid XI by season total points; bench ordered by points."""
    roster = sorted(roster_players(db, team).values(), key=lambda p: p.total_points, reverse=True)
    if len(roster) < 15:
        raise LineupError("Team roster is incomplete; cannot generate a lineup")

    gks = [p for p in roster if p.position == "GK"]
    outfield = [p for p in roster if p.position != "GK"]

    starters = [gks[0]]
    counts = {"DEF": 0, "MID": 0, "FWD": 0}
    maxes = {"DEF": 5, "MID": 5, "FWD": 3}
    # greedy fill by points, then fix minimums by swapping in the best of any underfilled position
    for p in outfield:
        if len(starters) < XI and counts[p.position] < maxes[p.position]:
            starters.append(p)
            counts[p.position] += 1
    mins = {"DEF": 3, "MID": 2, "FWD": 1}
    for pos, lo in mins.items():
        while counts[pos] < lo:
            candidate = next(p for p in outfield if p not in starters and p.position == pos)
            # drop the weakest starter whose position stays above its minimum
            for weakest in reversed(starters[1:]):
                if counts[weakest.position] > mins[weakest.position]:
                    starters.remove(weakest)
                    counts[weakest.position] -= 1
                    starters.append(candidate)
                    counts[pos] += 1
                    break

    starter_ids = [p.id for p in starters]
    bench = [p for p in roster if p.id not in starter_ids]
    bench_gk = next(p for p in bench if p.position == "GK")
    bench_outfield = [p for p in bench if p.position != "GK"]

    # starters[0] is always the GK, so the two best outfield starters get the armbands
    return set_lineup(
        db, team, gameweek,
        starter_ids,
        [bench_gk.id] + [p.id for p in bench_outfield],
        captain_id=starters[1].id,
        vice_id=starters[2].id,
        enforce_deadline=False,
    )
