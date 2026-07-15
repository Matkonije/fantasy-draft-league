"""Trade engine: proposals, 1.5x fairness check, league voting, execution."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import (
    Draft,
    DraftPick,
    FantasyLeague,
    LineupSlot,
    Notification,
    Player,
    Team,
    TeamGameweekScore,
    Trade,
    TradeVote,
)
from app.services.draft import POSITION_LIMITS

FAIRNESS_THRESHOLD = 1.5
VOTING_HOURS = 48


class TradeError(Exception):
    """Rule violation; message is safe to show to the user."""


def player_rating(player: Player) -> float:
    return max(player.price or 0.0, 0.0) + player.total_points / 10


def package_ratio(side_a: list[Player], side_b: list[Player]) -> float:
    a = max(sum(player_rating(p) for p in side_a), 0.1)
    b = max(sum(player_rating(p) for p in side_b), 0.1)
    return max(a, b) / min(a, b)


def notify(db: Session, user_ids: list[int], type_: str, message: str, data: dict) -> None:
    for uid in set(user_ids):
        db.add(Notification(user_id=uid, type=type_, message=message, data=data))


def _league_user_ids(db: Session, fantasy_league_id: int) -> list[int]:
    return list(db.scalars(select(Team.user_id).where(Team.fantasy_league_id == fantasy_league_id)))


def current_period_draft(db: Session, fantasy_league_id: int) -> Draft:
    draft = db.scalar(
        select(Draft)
        .where(Draft.fantasy_league_id == fantasy_league_id, Draft.status == "completed")
        .order_by(Draft.completed_at.desc())
    )
    if draft is None:
        raise TradeError("League has no completed draft yet")
    return draft


def _team_picks(db: Session, draft_id: int, team_id: int) -> dict[int, DraftPick]:
    picks = db.scalars(
        select(DraftPick).where(DraftPick.draft_id == draft_id, DraftPick.team_id == team_id)
    ).all()
    return {p.player_id: p for p in picks}


def _completed_trades_in_period(db: Session, draft_id: int, team_id: int) -> int:
    return len(
        db.scalars(
            select(Trade.id).where(
                Trade.draft_id == draft_id,
                Trade.status == "completed",
                (Trade.proposer_team_id == team_id) | (Trade.receiver_team_id == team_id),
            )
        ).all()
    )


def _validate(
    db: Session,
    fl: FantasyLeague,
    draft: Draft,
    proposer: Team,
    receiver: Team,
    give_ids: list[int],
    get_ids: list[int],
) -> tuple[list[Player], list[Player]]:
    if proposer.id == receiver.id:
        raise TradeError("Cannot trade with yourself")
    if receiver.fantasy_league_id != fl.id or proposer.fantasy_league_id != fl.id:
        raise TradeError("Both teams must belong to this fantasy league")

    if draft.completed_at is not None:
        window_end = draft.completed_at + timedelta(days=fl.trade_window_days)
        if datetime.now(timezone.utc) > window_end:
            raise TradeError("Trade window for this period is closed")

    for team in (proposer, receiver):
        if _completed_trades_in_period(db, draft.id, team.id) >= fl.max_trades_per_period:
            raise TradeError(f"Team '{team.name}' has reached the trade limit for this period")

    if not (1 <= len(give_ids) <= 3) or len(give_ids) != len(get_ids):
        raise TradeError("Trades must exchange an equal number of players, 1 to 3 per side")
    if len(set(give_ids)) != len(give_ids) or len(set(get_ids)) != len(get_ids):
        raise TradeError("Duplicate players in trade")

    proposer_picks = _team_picks(db, draft.id, proposer.id)
    receiver_picks = _team_picks(db, draft.id, receiver.id)
    if not set(give_ids) <= set(proposer_picks):
        raise TradeError("Proposer does not own all offered players")
    if not set(get_ids) <= set(receiver_picks):
        raise TradeError("Receiver does not own all requested players")

    players = {
        p.id: p for p in db.scalars(select(Player).where(Player.id.in_(give_ids + get_ids)))
    }

    # both rosters must satisfy squad quotas after the swap
    for team, picks, out_ids, in_ids in (
        (proposer, proposer_picks, give_ids, get_ids),
        (receiver, receiver_picks, get_ids, give_ids),
    ):
        roster_ids = (set(picks) - set(out_ids)) | set(in_ids)
        all_players = {
            p.id: p for p in db.scalars(select(Player).where(Player.id.in_(roster_ids)))
        }
        counts = {pos: 0 for pos in POSITION_LIMITS}
        for pid in roster_ids:
            counts[all_players[pid].position] += 1
        for pos, (lo, hi) in POSITION_LIMITS.items():
            if not lo <= counts[pos] <= hi:
                raise TradeError(
                    f"Trade would leave team '{team.name}' with {counts[pos]} {pos} "
                    f"(allowed {lo}-{hi})"
                )

    return [players[pid] for pid in give_ids], [players[pid] for pid in get_ids]


def propose(
    db: Session, fl: FantasyLeague, proposer: Team, receiver: Team,
    give_ids: list[int], get_ids: list[int],
) -> Trade:
    draft = current_period_draft(db, fl.id)
    give, get = _validate(db, fl, draft, proposer, receiver, give_ids, get_ids)

    trade = Trade(
        fantasy_league_id=fl.id,
        draft_id=draft.id,
        proposer_team_id=proposer.id,
        receiver_team_id=receiver.id,
        players_from_proposer=give_ids,
        players_from_receiver=get_ids,
        fairness_ratio=round(package_ratio(give, get), 3),
    )
    db.add(trade)
    db.flush()
    notify(
        db, [receiver.user_id], "trade_proposed",
        f"Team '{proposer.name}' proposed a trade to you",
        {"trade_id": trade.id},
    )
    db.commit()
    db.refresh(trade)
    return trade


def accept(db: Session, trade: Trade) -> Trade:
    if trade.status != "proposed":
        raise TradeError(f"Trade cannot be accepted from status '{trade.status}'")

    fl = db.get(FantasyLeague, trade.fantasy_league_id)
    draft = db.get(Draft, trade.draft_id)
    proposer = db.get(Team, trade.proposer_team_id)
    receiver = db.get(Team, trade.receiver_team_id)
    give, get = _validate(
        db, fl, draft, proposer, receiver,
        trade.players_from_proposer, trade.players_from_receiver,
    )
    trade.fairness_ratio = round(package_ratio(give, get), 3)

    if trade.fairness_ratio <= FAIRNESS_THRESHOLD:
        _execute(db, trade, fl, proposer, receiver)
    else:
        trade.status = "voting"
        trade.voting_deadline = datetime.now(timezone.utc) + timedelta(hours=VOTING_HOURS)
        notify(
            db, _league_user_ids(db, fl.id), "trade_voting",
            f"Trade between '{proposer.name}' and '{receiver.name}' flagged as unfair "
            f"(ratio {trade.fairness_ratio}); league vote is open",
            {"trade_id": trade.id},
        )
    db.commit()
    db.refresh(trade)
    return trade


def reject(db: Session, trade: Trade, *, by: str, reason: str = "") -> Trade:
    if trade.status not in ("proposed", "voting"):
        raise TradeError(f"Trade cannot be rejected from status '{trade.status}'")
    trade.status = "cancelled" if by == "proposer" else "rejected"
    trade.resolved_at = datetime.now(timezone.utc)
    proposer = db.get(Team, trade.proposer_team_id)
    receiver = db.get(Team, trade.receiver_team_id)
    notify(
        db, [proposer.user_id, receiver.user_id], "trade_resolved",
        f"Trade between '{proposer.name}' and '{receiver.name}' was {trade.status}"
        + (f" ({reason})" if reason else ""),
        {"trade_id": trade.id},
    )
    db.commit()
    db.refresh(trade)
    return trade


def vote(db: Session, trade: Trade, voting_team: Team, approve: bool) -> Trade:
    if trade.status != "voting":
        raise TradeError("Trade is not open for voting")
    if voting_team.id in (trade.proposer_team_id, trade.receiver_team_id):
        raise TradeError("Teams involved in the trade cannot vote")
    if voting_team.fantasy_league_id != trade.fantasy_league_id:
        raise TradeError("Only teams from this league can vote")
    existing = db.scalar(
        select(TradeVote).where(TradeVote.trade_id == trade.id, TradeVote.team_id == voting_team.id)
    )
    if existing:
        raise TradeError("This team has already voted")

    db.add(TradeVote(trade_id=trade.id, team_id=voting_team.id, approve=approve))
    db.flush()
    _resolve_votes(db, trade)
    db.commit()
    db.refresh(trade)
    return trade


def _resolve_votes(db: Session, trade: Trade) -> None:
    fl = db.get(FantasyLeague, trade.fantasy_league_id)
    all_team_ids = set(
        db.scalars(select(Team.id).where(Team.fantasy_league_id == fl.id))
    )
    eligible = len(all_team_ids - {trade.proposer_team_id, trade.receiver_team_id})
    votes = db.scalars(select(TradeVote).where(TradeVote.trade_id == trade.id)).all()
    approvals = sum(1 for v in votes if v.approve)
    rejections = len(votes) - approvals

    if approvals * 2 > eligible:
        proposer = db.get(Team, trade.proposer_team_id)
        receiver = db.get(Team, trade.receiver_team_id)
        _execute(db, trade, fl, proposer, receiver)
    elif rejections * 2 > eligible:
        trade.status = "rejected"
        trade.resolved_at = datetime.now(timezone.utc)
        notify(
            db, _league_user_ids(db, fl.id), "trade_resolved",
            "Flagged trade was rejected by league vote", {"trade_id": trade.id},
        )


def _execute(db: Session, trade: Trade, fl: FantasyLeague, proposer: Team, receiver: Team) -> None:
    proposer_picks = _team_picks(db, trade.draft_id, proposer.id)
    receiver_picks = _team_picks(db, trade.draft_id, receiver.id)
    for pid in trade.players_from_proposer:
        proposer_picks[pid].team_id = receiver.id
    for pid in trade.players_from_receiver:
        receiver_picks[pid].team_id = proposer.id

    # wipe lineups for unscored gameweeks so defaults regenerate with the new rosters
    for team_id in (proposer.id, receiver.id):
        scored = select(TeamGameweekScore.gameweek).where(TeamGameweekScore.team_id == team_id)
        db.execute(
            delete(LineupSlot).where(
                LineupSlot.team_id == team_id, LineupSlot.gameweek.not_in(scored)
            )
        )

    trade.status = "completed"
    trade.resolved_at = datetime.now(timezone.utc)
    notify(
        db, _league_user_ids(db, fl.id), "trade_completed",
        f"Trade between '{proposer.name}' and '{receiver.name}' completed "
        f"(fairness ratio {trade.fairness_ratio})",
        {"trade_id": trade.id},
    )


def expire_overdue(db: Session) -> list[int]:
    """Reject voting trades whose deadline passed. Returns affected trade ids."""
    now = datetime.now(timezone.utc)
    overdue = db.scalars(
        select(Trade).where(Trade.status == "voting", Trade.voting_deadline < now)
    ).all()
    for trade in overdue:
        trade.status = "rejected"
        trade.resolved_at = now
        notify(
            db, _league_user_ids(db, trade.fantasy_league_id), "trade_resolved",
            "Flagged trade was rejected: voting deadline expired without a majority",
            {"trade_id": trade.id},
        )
    if overdue:
        db.commit()
    return [t.id for t in overdue]
