from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.models import Draft, DraftPick, FantasyLeague, Player, Team, User
from app.schemas.fantasy import DraftStateOut, PickRequest, RosterOut
from app.schemas.player import PlayerListOut, PlayerOut
from app.services import draft as draft_service
from app.services.auth import get_current_user
from app.services.draft import DraftError
from app.services.ws import manager
from jose import JWTError, jwt

from app.config import settings

router = APIRouter(tags=["drafts"])


def _get_draft(db: Session, draft_id: int) -> Draft:
    draft = db.get(Draft, draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


def _require_commissioner(db: Session, draft: Draft, user: User) -> FantasyLeague:
    fl = db.get(FantasyLeague, draft.fantasy_league_id)
    if fl.commissioner_id != user.id:
        raise HTTPException(status_code=403, detail="Only the league commissioner can do this")
    return fl


def _state(db: Session, draft: Draft) -> DraftStateOut:
    picks = db.scalars(
        select(DraftPick).where(DraftPick.draft_id == draft.id).order_by(DraftPick.pick_number)
    ).all()
    return DraftStateOut(
        id=draft.id,
        fantasy_league_id=draft.fantasy_league_id,
        status=draft.status,
        rounds=draft.rounds,
        draft_order=draft.draft_order,
        current_pick_index=draft.current_pick_index,
        current_team_id=draft_service.team_on_the_clock(draft),
        current_pick_deadline=draft.current_pick_deadline,
        server_time=datetime.now(timezone.utc),
        picks=picks,
    )


@router.post(
    "/fantasy-leagues/{fantasy_league_id}/drafts",
    response_model=DraftStateOut,
    status_code=status.HTTP_201_CREATED,
)
def create_draft(
    fantasy_league_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    fl = db.scalar(select(FantasyLeague).where(FantasyLeague.id == fantasy_league_id))
    if fl is None:
        raise HTTPException(status_code=404, detail="Fantasy league not found")
    if fl.commissioner_id != user.id:
        raise HTTPException(status_code=403, detail="Only the league commissioner can do this")
    try:
        draft = draft_service.create_draft(db, fl)
    except DraftError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return _state(db, draft)


@router.post("/drafts/{draft_id}/start", response_model=DraftStateOut)
async def start_draft(
    draft_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    draft = _get_draft(db, draft_id)
    fl = _require_commissioner(db, draft, user)
    try:
        draft_service.start_draft(db, draft, fl.pick_timer_seconds)
    except DraftError as e:
        raise HTTPException(status_code=409, detail=str(e))
    await manager.broadcast(
        draft.id,
        {
            "type": "draft_started",
            "draft_id": draft.id,
            "next_team_id": draft_service.team_on_the_clock(draft),
            "deadline": draft.current_pick_deadline.isoformat(),
        },
    )
    return _state(db, draft)


@router.get("/drafts/{draft_id}", response_model=DraftStateOut)
def draft_state(draft_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return _state(db, _get_draft(db, draft_id))


@router.post("/drafts/{draft_id}/pick", response_model=DraftStateOut)
async def pick(
    draft_id: int,
    body: PickRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    draft = _get_draft(db, draft_id)
    team = db.scalar(
        select(Team).where(
            Team.fantasy_league_id == draft.fantasy_league_id, Team.user_id == user.id
        )
    )
    if team is None:
        raise HTTPException(status_code=403, detail="You do not have a team in this draft")
    player = db.get(Player, body.player_id)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    try:
        event = draft_service.make_pick(db, draft, team, player)
    except DraftError as e:
        raise HTTPException(status_code=409, detail=str(e))
    await manager.broadcast(draft.id, event)
    if event["draft_status"] == "completed":
        await manager.broadcast(draft.id, {"type": "draft_completed", "draft_id": draft.id})
    return _state(db, draft)


@router.post("/drafts/{draft_id}/force-pick", response_model=DraftStateOut)
async def force_pick(
    draft_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    draft = _get_draft(db, draft_id)
    _require_commissioner(db, draft, user)
    try:
        event = draft_service.auto_pick(db, draft)
    except DraftError as e:
        raise HTTPException(status_code=409, detail=str(e))
    await manager.broadcast(draft.id, event)
    if event["draft_status"] == "completed":
        await manager.broadcast(draft.id, {"type": "draft_completed", "draft_id": draft.id})
    return _state(db, draft)


@router.get("/drafts/{draft_id}/available-players", response_model=PlayerListOut)
def available_players(
    draft_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    position: str | None = Query(None, pattern="^(GK|DEF|MID|FWD)$"),
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    draft = _get_draft(db, draft_id)
    fl = db.get(FantasyLeague, draft.fantasy_league_id)
    picked = select(DraftPick.player_id).where(DraftPick.draft_id == draft.id)

    query = select(Player).where(Player.league_id == fl.league_id, Player.id.not_in(picked))
    if position:
        query = query.where(Player.position == position)
    if search:
        query = query.where(Player.name.ilike(f"%{search}%"))

    from sqlalchemy import func

    total = db.scalar(select(func.count()).select_from(query.subquery()))
    items = db.scalars(
        query.order_by(Player.total_points.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return PlayerListOut(total=total, page=page, page_size=page_size, items=items)


@router.get("/teams/{team_id}/roster", response_model=RosterOut)
def team_roster(team_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    players = db.scalars(
        select(Player)
        .join(DraftPick, DraftPick.player_id == Player.id)
        .join(Draft, Draft.id == DraftPick.draft_id)
        .where(
            DraftPick.team_id == team.id,
            Draft.status.in_(["active", "completed"]),
            Draft.fantasy_league_id == team.fantasy_league_id,
        )
        .order_by(Player.position, Player.total_points.desc())
    ).all()
    return RosterOut(team=team, players=[PlayerOut.model_validate(p) for p in players])


@router.websocket("/drafts/{draft_id}/ws")
async def draft_ws(websocket: WebSocket, draft_id: int, token: str = Query(...)):
    # authenticate via ?token= (browsers cannot set headers on WebSocket)
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        await websocket.close(code=4401)
        return

    with SessionLocal() as db:
        if db.get(Draft, draft_id) is None or db.get(User, user_id) is None:
            await websocket.close(code=4404)
            return

    await manager.connect(draft_id, websocket)
    try:
        while True:
            await websocket.receive_text()  # keepalive; client messages are ignored
    except WebSocketDisconnect:
        await manager.disconnect(draft_id, websocket)
