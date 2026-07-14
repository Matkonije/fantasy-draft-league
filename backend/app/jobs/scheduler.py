"""Hourly FPL sync: schedule, finished-gameweek stats and scoring."""

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.database import SessionLocal
from app.models import Gameweek, League, TeamGameweekScore
from app.jobs import sync
from app.services.scoring import compute_gameweek_scores

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def hourly_fpl_sync() -> None:
    try:
        with SessionLocal() as db:
            sync.sync_players(db)
            sync.sync_gameweeks(db)

            league = db.scalar(select(League).where(League.code == "PL"))
            if league is None:
                return
            finished = db.scalars(
                select(Gameweek).where(Gameweek.league_id == league.id, Gameweek.finished)
            ).all()
            for gw in finished:
                already = db.scalar(
                    select(TeamGameweekScore).where(TeamGameweekScore.gameweek == gw.number)
                )
                if already:
                    continue
                result = sync.sync_gameweek(db, gw.number)
                if result.get("synced"):
                    summary = compute_gameweek_scores(db, league.id, gw.number)
                    logger.info("Scored GW %s: %s", gw.number, summary)
    except Exception:
        logger.exception("Hourly FPL sync failed")


async def _hourly_job() -> None:
    # sync job does blocking HTTP + DB work; keep it off the event loop
    await asyncio.to_thread(hourly_fpl_sync)


def start_scheduler() -> None:
    scheduler.add_job(_hourly_job, "interval", minutes=60, id="fpl_sync")
    scheduler.start()


def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)
