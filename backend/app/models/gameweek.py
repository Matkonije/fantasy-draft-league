from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Gameweek(Base):
    __tablename__ = "gameweeks"
    __table_args__ = (UniqueConstraint("league_id", "number", name="uq_gameweek_league_number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), index=True)
    number: Mapped[int] = mapped_column()
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished: Mapped[bool] = mapped_column(default=False)


class LineupSlot(Base):
    __tablename__ = "lineup_slots"
    __table_args__ = (
        UniqueConstraint("team_id", "gameweek", "player_id", name="uq_lineup_team_gw_player"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)
    gameweek: Mapped[int] = mapped_column(index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    role: Mapped[str] = mapped_column(String(10))  # starter / bench
    bench_order: Mapped[int] = mapped_column(default=0)  # bench: 0 = GK, 1-3 = outfield order
    is_captain: Mapped[bool] = mapped_column(default=False)
    is_vice: Mapped[bool] = mapped_column(default=False)


class TeamGameweekScore(Base):
    __tablename__ = "team_gameweek_scores"
    __table_args__ = (UniqueConstraint("team_id", "gameweek", name="uq_score_team_gameweek"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)
    gameweek: Mapped[int] = mapped_column(index=True)
    points: Mapped[int] = mapped_column(default=0)
    breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
