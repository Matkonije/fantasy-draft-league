from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import FantasyLeague, Team, Trade, User
from app.schemas.trade import TradeOut, TradePropose, TradeVoteIn
from app.services import trade as trade_service
from app.services.auth import get_current_user
from app.services.trade import TradeError

router = APIRouter(tags=["trades"])


def _get_trade(db: Session, trade_id: int) -> Trade:
    trade = db.scalar(
        select(Trade).where(Trade.id == trade_id).options(selectinload(Trade.votes))
    )
    if trade is None:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade


def _user_team(db: Session, fantasy_league_id: int, user: User) -> Team:
    team = db.scalar(
        select(Team).where(
            Team.fantasy_league_id == fantasy_league_id, Team.user_id == user.id
        )
    )
    if team is None:
        raise HTTPException(status_code=403, detail="You do not have a team in this league")
    return team


@router.post(
    "/fantasy-leagues/{fantasy_league_id}/trades",
    response_model=TradeOut,
    status_code=status.HTTP_201_CREATED,
)
def propose_trade(
    fantasy_league_id: int,
    body: TradePropose,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    fl = db.get(FantasyLeague, fantasy_league_id)
    if fl is None:
        raise HTTPException(status_code=404, detail="Fantasy league not found")
    proposer = _user_team(db, fl.id, user)
    receiver = db.get(Team, body.receiver_team_id)
    if receiver is None:
        raise HTTPException(status_code=404, detail="Receiver team not found")
    try:
        return trade_service.propose(
            db, fl, proposer, receiver, body.players_from_proposer, body.players_from_receiver
        )
    except TradeError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/fantasy-leagues/{fantasy_league_id}/trades", response_model=list[TradeOut])
def list_trades(
    fantasy_league_id: int,
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = (
        select(Trade)
        .where(Trade.fantasy_league_id == fantasy_league_id)
        .options(selectinload(Trade.votes))
        .order_by(Trade.created_at.desc())
    )
    if status_filter:
        query = query.where(Trade.status == status_filter)
    return db.scalars(query).all()


@router.get("/trades/{trade_id}", response_model=TradeOut)
def trade_detail(trade_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return _get_trade(db, trade_id)


@router.post("/trades/{trade_id}/accept", response_model=TradeOut)
def accept_trade(trade_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    trade = _get_trade(db, trade_id)
    receiver = db.get(Team, trade.receiver_team_id)
    if receiver.user_id != user.id:
        raise HTTPException(status_code=403, detail="Only the receiving team can accept")
    try:
        return trade_service.accept(db, trade)
    except TradeError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/trades/{trade_id}/reject", response_model=TradeOut)
def reject_trade(trade_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    trade = _get_trade(db, trade_id)
    receiver = db.get(Team, trade.receiver_team_id)
    if receiver.user_id != user.id:
        raise HTTPException(status_code=403, detail="Only the receiving team can reject")
    try:
        return trade_service.reject(db, trade, by="receiver")
    except TradeError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/trades/{trade_id}/cancel", response_model=TradeOut)
def cancel_trade(trade_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    trade = _get_trade(db, trade_id)
    if trade.status != "proposed":
        raise HTTPException(status_code=409, detail="Only proposed trades can be cancelled")
    proposer = db.get(Team, trade.proposer_team_id)
    if proposer.user_id != user.id:
        raise HTTPException(status_code=403, detail="Only the proposing team can cancel")
    try:
        return trade_service.reject(db, trade, by="proposer")
    except TradeError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/trades/{trade_id}/vote", response_model=TradeOut)
def vote_trade(
    trade_id: int,
    body: TradeVoteIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trade = _get_trade(db, trade_id)
    team = _user_team(db, trade.fantasy_league_id, user)
    if team.id in (trade.proposer_team_id, trade.receiver_team_id):
        raise HTTPException(status_code=403, detail="Teams involved in the trade cannot vote")
    try:
        return trade_service.vote(db, trade, team, body.approve)
    except TradeError as e:
        raise HTTPException(status_code=409, detail=str(e))
