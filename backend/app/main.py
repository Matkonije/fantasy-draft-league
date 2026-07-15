import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.jobs.scheduler import start_scheduler, stop_scheduler
from app.routers import (
    admin,
    auth,
    drafts,
    fantasy_leagues,
    leagues,
    lineups,
    notifications,
    players,
    trades,
)
from app.services.draft_timer import watch_deadlines


@asynccontextmanager
async def lifespan(app: FastAPI):
    timer_task = asyncio.create_task(watch_deadlines())
    start_scheduler()
    yield
    stop_scheduler()
    timer_task.cancel()


app = FastAPI(title="Fantasy Draft League", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server (frontend, later phase)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(players.router)
app.include_router(leagues.router)
app.include_router(fantasy_leagues.router)
app.include_router(drafts.router)
app.include_router(lineups.router)
app.include_router(trades.router)
app.include_router(notifications.router)
app.include_router(admin.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
