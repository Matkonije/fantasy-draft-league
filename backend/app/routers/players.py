from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Player, User
from app.schemas.player import PlayerDetailOut, PlayerListOut
from app.services.auth import get_current_user

router = APIRouter(prefix="/players", tags=["players"])

SORT_COLUMNS = {
    "total_points": Player.total_points,
    "price": Player.price,
    "name": Player.name,
}


@router.get("", response_model=PlayerListOut)
def list_players(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    position: str | None = Query(None, pattern="^(GK|DEF|MID|FWD)$"),
    club: str | None = None,
    search: str | None = None,
    league_id: int | None = None,
    sort: str = Query("total_points", pattern="^(total_points|price|name)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    query = select(Player)
    if position:
        query = query.where(Player.position == position)
    if club:
        query = query.where(Player.club.ilike(f"%{club}%"))
    if search:
        query = query.where(Player.name.ilike(f"%{search}%"))
    if league_id:
        query = query.where(Player.league_id == league_id)

    total = db.scalar(select(func.count()).select_from(query.subquery()))
    col = SORT_COLUMNS[sort]
    query = query.order_by(col.asc() if order == "asc" else col.desc())
    items = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()

    return PlayerListOut(total=total, page=page, page_size=page_size, items=items)


@router.get("/{player_id}", response_model=PlayerDetailOut)
def get_player(player_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    player = db.scalar(
        select(Player).where(Player.id == player_id).options(selectinload(Player.stats))
    )
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    player.stats.sort(key=lambda s: s.gameweek)
    return player
