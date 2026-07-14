from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Draft, FantasyLeague, League, Team, User
from app.schemas.fantasy import FantasyLeagueCreate, FantasyLeagueJoin, FantasyLeagueOut
from app.services.auth import get_current_user
from app.services.draft import generate_invite_code

router = APIRouter(prefix="/fantasy-leagues", tags=["fantasy-leagues"])


def get_league_or_404(db: Session, fantasy_league_id: int) -> FantasyLeague:
    fl = db.scalar(
        select(FantasyLeague)
        .where(FantasyLeague.id == fantasy_league_id)
        .options(selectinload(FantasyLeague.teams))
    )
    if fl is None:
        raise HTTPException(status_code=404, detail="Fantasy league not found")
    return fl


@router.post("", response_model=FantasyLeagueOut, status_code=status.HTTP_201_CREATED)
def create_fantasy_league(
    body: FantasyLeagueCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    if db.get(League, body.league_id) is None:
        raise HTTPException(status_code=404, detail="Football league not found")

    fl = FantasyLeague(
        name=body.name,
        league_id=body.league_id,
        invite_code=generate_invite_code(),
        commissioner_id=user.id,
        pick_timer_seconds=body.pick_timer_seconds,
    )
    db.add(fl)
    db.flush()
    db.add(Team(fantasy_league_id=fl.id, user_id=user.id, name=body.team_name))
    db.commit()
    return get_league_or_404(db, fl.id)


@router.post("/join", response_model=FantasyLeagueOut)
def join_fantasy_league(
    body: FantasyLeagueJoin, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    fl = db.scalar(select(FantasyLeague).where(FantasyLeague.invite_code == body.invite_code))
    if fl is None:
        raise HTTPException(status_code=404, detail="Invalid invite code")

    existing = db.scalar(
        select(Team).where(Team.fantasy_league_id == fl.id, Team.user_id == user.id)
    )
    if existing:
        raise HTTPException(status_code=409, detail="You already have a team in this league")

    draft_exists = db.scalar(
        select(Draft).where(
            Draft.fantasy_league_id == fl.id, Draft.status.in_(["active", "completed"])
        )
    )
    if draft_exists:
        raise HTTPException(status_code=409, detail="Cannot join: this league has already drafted")

    db.add(Team(fantasy_league_id=fl.id, user_id=user.id, name=body.team_name))
    db.commit()
    return get_league_or_404(db, fl.id)


@router.get("", response_model=list[FantasyLeagueOut])
def my_fantasy_leagues(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ids = select(Team.fantasy_league_id).where(Team.user_id == user.id)
    return db.scalars(
        select(FantasyLeague)
        .where(FantasyLeague.id.in_(ids))
        .options(selectinload(FantasyLeague.teams))
    ).all()


@router.get("/{fantasy_league_id}", response_model=FantasyLeagueOut)
def fantasy_league_detail(
    fantasy_league_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    return get_league_or_404(db, fantasy_league_id)
