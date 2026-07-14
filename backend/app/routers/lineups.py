from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Team, User
from app.schemas.lineup import LineupOut, LineupSet
from app.services import lineup as lineup_service
from app.services.auth import get_current_user
from app.services.lineup import LineupError

router = APIRouter(tags=["lineups"])


def _get_team(db: Session, team_id: int) -> Team:
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.get("/teams/{team_id}/lineup", response_model=LineupOut)
def get_lineup(
    team_id: int,
    gameweek: int = Query(ge=1, le=38),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    team = _get_team(db, team_id)
    slots = lineup_service.get_lineup(db, team.id, gameweek)
    return LineupOut(team_id=team.id, gameweek=gameweek, slots=slots)


@router.put("/teams/{team_id}/lineup", response_model=LineupOut)
def set_lineup(
    team_id: int,
    body: LineupSet,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    team = _get_team(db, team_id)
    if team.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your team")
    try:
        slots = lineup_service.set_lineup(
            db, team, body.gameweek, body.starters, body.bench, body.captain_id, body.vice_id
        )
    except LineupError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return LineupOut(team_id=team.id, gameweek=body.gameweek, slots=slots)
