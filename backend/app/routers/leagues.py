from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import League, User
from app.schemas.player import LeagueOut
from app.services.auth import get_current_user

router = APIRouter(prefix="/leagues", tags=["leagues"])


@router.get("", response_model=list[LeagueOut])
def list_leagues(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.scalars(select(League)).all()
