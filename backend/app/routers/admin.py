from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.jobs import sync
from app.models import User
from app.services.auth import get_current_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/sync/players")
def trigger_sync_players(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    try:
        return sync.sync_players(db)
    except Exception as e:  # surface FPL API failures as a clean 502
        raise HTTPException(status_code=502, detail=f"FPL sync failed: {e}")


@router.post("/sync/gameweek/{gameweek}")
def trigger_sync_gameweek(
    gameweek: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)
):
    if not 1 <= gameweek <= 38:
        raise HTTPException(status_code=400, detail="Gameweek must be between 1 and 38")
    try:
        return sync.sync_gameweek(db, gameweek)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"FPL sync failed: {e}")
