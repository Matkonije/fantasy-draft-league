"""Background watcher: auto-picks for teams whose pick timer expired."""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Draft
from app.services import draft as draft_service
from app.services.ws import manager

logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 1.0


def _expired_auto_picks() -> list[dict]:
    """Run auto-picks for all expired deadlines. Sync DB work, called off the event loop."""
    events: list[dict] = []
    with SessionLocal() as db:
        now = datetime.now(timezone.utc)
        drafts = db.scalars(
            select(Draft).where(Draft.status == "active", Draft.current_pick_deadline < now)
        ).all()
        for d in drafts:
            try:
                events.append(draft_service.auto_pick(db, d))
            except draft_service.DraftError as e:
                logger.warning("Auto-pick failed for draft %s: %s", d.id, e)
    return events


async def watch_deadlines() -> None:
    while True:
        try:
            events = await asyncio.to_thread(_expired_auto_picks)
            for event in events:
                await manager.broadcast(event["draft_id"], event)
                if event["draft_status"] == "completed":
                    await manager.broadcast(
                        event["draft_id"],
                        {"type": "draft_completed", "draft_id": event["draft_id"]},
                    )
        except Exception:
            logger.exception("Draft timer loop iteration failed")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
