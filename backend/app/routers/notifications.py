from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Notification, User
from app.schemas.trade import MarkReadIn, NotificationOut
from app.services.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
def list_notifications(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = (
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(100)
    )
    if unread_only:
        query = query.where(Notification.read.is_(False))
    return db.scalars(query).all()


@router.post("/mark-read")
def mark_read(
    body: MarkReadIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    query = update(Notification).where(Notification.user_id == user.id).values(read=True)
    if body.ids:
        query = query.where(Notification.id.in_(body.ids))
    result = db.execute(query)
    db.commit()
    return {"marked_read": result.rowcount}
