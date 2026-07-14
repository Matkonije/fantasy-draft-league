"""Core snake-draft logic: order, turn math, roster feasibility, picking."""

import random
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Draft, DraftPick, FantasyLeague, Player, Team

# roster: 15 slots — starters 1 GK / 4 DEF / 4 MID / 2 FWD + bench 1 GK / 3 outfield
ROSTER_SIZE = 15
POSITION_LIMITS = {  # position -> (min, max) across the full 15-man squad
    "GK": (2, 2),
    "DEF": (4, 7),
    "MID": (4, 7),
    "FWD": (2, 5),
}


class DraftError(Exception):
    """Rule violation; message is safe to show to the user."""


def generate_invite_code() -> str:
    return secrets.token_urlsafe(6)[:8]


def team_on_the_clock(draft: Draft) -> int | None:
    """Team id whose turn it is, or None if the draft is over."""
    order = draft.draft_order
    n = len(order)
    if n == 0 or draft.current_pick_index >= n * draft.rounds:
        return None
    round_idx, idx = divmod(draft.current_pick_index, n)
    return order[idx] if round_idx % 2 == 0 else order[n - 1 - idx]


def create_draft(db: Session, fantasy_league: FantasyLeague) -> Draft:
    active = db.scalar(
        select(Draft).where(
            Draft.fantasy_league_id == fantasy_league.id,
            Draft.status.in_(["scheduled", "active"]),
        )
    )
    if active:
        raise DraftError("A draft is already scheduled or active for this league")

    team_ids = [t.id for t in fantasy_league.teams]
    if len(team_ids) < 2:
        raise DraftError("At least 2 teams are required to start a draft")

    # Phase 2 will order by reverse standings of the previous period;
    # with no scores yet the first draft order is random.
    random.shuffle(team_ids)

    draft = Draft(fantasy_league_id=fantasy_league.id, draft_order=team_ids, rounds=ROSTER_SIZE)
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


def start_draft(db: Session, draft: Draft, timer_seconds: int) -> None:
    if draft.status != "scheduled":
        raise DraftError(f"Draft cannot be started from status '{draft.status}'")
    draft.status = "active"
    draft.started_at = datetime.now(timezone.utc)
    draft.current_pick_deadline = draft.started_at + timedelta(seconds=timer_seconds)
    db.commit()


def roster_counts(db: Session, draft_id: int, team_id: int) -> dict[str, int]:
    rows = db.execute(
        select(Player.position)
        .join(DraftPick, DraftPick.player_id == Player.id)
        .where(DraftPick.draft_id == draft_id, DraftPick.team_id == team_id)
    ).all()
    counts = {pos: 0 for pos in POSITION_LIMITS}
    for (pos,) in rows:
        counts[pos] = counts.get(pos, 0) + 1
    return counts


def validate_position_feasible(counts: dict[str, int], position: str) -> None:
    """Reject a pick that would overfill a position or make the 15-man quota unreachable."""
    picked = sum(counts.values())
    if picked >= ROSTER_SIZE:
        raise DraftError("Roster is already full")
    if position not in POSITION_LIMITS:
        raise DraftError(f"Unknown position '{position}'")

    _, pos_max = POSITION_LIMITS[position]
    if counts[position] + 1 > pos_max:
        raise DraftError(f"Position limit reached: max {pos_max} {position} per squad")

    after = dict(counts)
    after[position] += 1
    remaining = ROSTER_SIZE - (picked + 1)
    still_needed = sum(max(0, lim[0] - after[pos]) for pos, lim in POSITION_LIMITS.items())
    if still_needed > remaining:
        raise DraftError(
            f"Picking a {position} now would make it impossible to fill minimum quotas "
            f"(need {still_needed} specific positions, only {remaining} picks left)"
        )


def make_pick(
    db: Session, draft: Draft, team: Team, player: Player, *, is_auto: bool = False
) -> dict:
    """Validate and record a pick, advance the draft. Returns a broadcastable event."""
    if draft.status != "active":
        raise DraftError("Draft is not active")
    if team_on_the_clock(draft) != team.id:
        raise DraftError("It is not this team's turn to pick")

    fl = db.get(FantasyLeague, draft.fantasy_league_id)
    if player.league_id != fl.league_id:
        raise DraftError("Player does not belong to this league's player pool")

    taken = db.scalar(
        select(DraftPick).where(DraftPick.draft_id == draft.id, DraftPick.player_id == player.id)
    )
    if taken:
        raise DraftError("Player has already been drafted")

    validate_position_feasible(roster_counts(db, draft.id, team.id), player.position)

    n = len(draft.draft_order)
    pick = DraftPick(
        draft_id=draft.id,
        team_id=team.id,
        player_id=player.id,
        round=draft.current_pick_index // n + 1,
        pick_number=draft.current_pick_index,
        is_auto=is_auto,
    )
    db.add(pick)

    draft.current_pick_index += 1
    if draft.current_pick_index >= n * draft.rounds:
        draft.status = "completed"
        draft.completed_at = datetime.now(timezone.utc)
        draft.current_pick_deadline = None
    else:
        draft.current_pick_deadline = datetime.now(timezone.utc) + timedelta(
            seconds=fl.pick_timer_seconds
        )
    db.commit()

    return {
        "type": "pick_made",
        "draft_id": draft.id,
        "pick_number": pick.pick_number,
        "round": pick.round,
        "team_id": team.id,
        "player": {"id": player.id, "name": player.name, "club": player.club, "position": player.position},
        "is_auto": is_auto,
        "draft_status": draft.status,
        "next_team_id": team_on_the_clock(draft),
        "deadline": draft.current_pick_deadline.isoformat() if draft.current_pick_deadline else None,
    }


def auto_pick(db: Session, draft: Draft) -> dict:
    """Pick the best available player (by last-season total points) for the team on the clock."""
    team_id = team_on_the_clock(draft)
    if team_id is None:
        raise DraftError("Draft has no current pick")
    team = db.get(Team, team_id)
    fl = db.get(FantasyLeague, draft.fantasy_league_id)

    counts = roster_counts(db, draft.id, team_id)
    picked_ids = select(DraftPick.player_id).where(DraftPick.draft_id == draft.id)
    candidates = db.scalars(
        select(Player)
        .where(Player.league_id == fl.league_id, Player.id.not_in(picked_ids))
        .order_by(Player.total_points.desc())
        .limit(200)
    ).all()

    for player in candidates:
        try:
            validate_position_feasible(counts, player.position)
        except DraftError:
            continue
        return make_pick(db, draft, team, player, is_auto=True)

    raise DraftError("No eligible player found for auto-pick")
