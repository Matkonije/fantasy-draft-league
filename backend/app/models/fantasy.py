from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FantasyLeague(Base):
    __tablename__ = "fantasy_leagues"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"))  # football league (PL, ...)
    invite_code: Mapped[str] = mapped_column(String(12), unique=True, index=True)
    commissioner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    pick_timer_seconds: Mapped[int] = mapped_column(default=90)
    trade_window_days: Mapped[int] = mapped_column(default=3, server_default="3")
    max_trades_per_period: Mapped[int] = mapped_column(default=2, server_default="2")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    teams: Mapped[list["Team"]] = relationship(back_populates="fantasy_league")


class Team(Base):
    __tablename__ = "teams"
    __table_args__ = (UniqueConstraint("fantasy_league_id", "user_id", name="uq_team_league_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    fantasy_league_id: Mapped[int] = mapped_column(ForeignKey("fantasy_leagues.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    fantasy_league: Mapped[FantasyLeague] = relationship(back_populates="teams")


class Draft(Base):
    __tablename__ = "drafts"

    id: Mapped[int] = mapped_column(primary_key=True)
    fantasy_league_id: Mapped[int] = mapped_column(ForeignKey("fantasy_leagues.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="scheduled")  # scheduled/active/completed/cancelled
    rounds: Mapped[int] = mapped_column(default=15)
    # first-round team order; snake order is derived from it
    draft_order: Mapped[list] = mapped_column(JSON, default=list)
    current_pick_index: Mapped[int] = mapped_column(default=0)
    current_pick_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    picks: Mapped[list["DraftPick"]] = relationship(back_populates="draft")


class DraftPick(Base):
    __tablename__ = "draft_picks"
    __table_args__ = (
        UniqueConstraint("draft_id", "player_id", name="uq_draft_player"),
        UniqueConstraint("draft_id", "pick_number", name="uq_draft_pick_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    draft_id: Mapped[int] = mapped_column(ForeignKey("drafts.id"), index=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    round: Mapped[int] = mapped_column()
    pick_number: Mapped[int] = mapped_column()  # overall, 0-based
    is_auto: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    draft: Mapped[Draft] = relationship(back_populates="picks")
