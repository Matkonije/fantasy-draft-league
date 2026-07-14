from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    club: Mapped[str] = mapped_column(String(80), index=True)
    position: Mapped[str] = mapped_column(String(3), index=True)  # GK / DEF / MID / FWD
    status: Mapped[str] = mapped_column(String(20), default="available")

    # external ids
    fpl_id: Mapped[int | None] = mapped_column(Integer, unique=True)
    source_a_id: Mapped[str | None] = mapped_column(String(50))  # football-data / API-Football
    source_b_id: Mapped[str | None] = mapped_column(String(50))  # understat
    tm_id: Mapped[str | None] = mapped_column(String(50))  # transfermarkt

    price: Mapped[float | None] = mapped_column(Float)  # FPL now_cost / 10
    total_points: Mapped[int] = mapped_column(default=0)

    stats: Mapped[list["PlayerStatsWeekly"]] = relationship(back_populates="player")


class PlayerStatsWeekly(Base):
    __tablename__ = "player_stats_weekly"
    __table_args__ = (UniqueConstraint("player_id", "gameweek", name="uq_player_gameweek"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)
    gameweek: Mapped[int] = mapped_column(index=True)

    minutes: Mapped[int] = mapped_column(default=0)
    goals: Mapped[int] = mapped_column(default=0)
    assists: Mapped[int] = mapped_column(default=0)
    clean_sheets: Mapped[int] = mapped_column(default=0)
    goals_conceded: Mapped[int] = mapped_column(default=0)
    yellow_cards: Mapped[int] = mapped_column(default=0)
    red_cards: Mapped[int] = mapped_column(default=0)
    saves: Mapped[int] = mapped_column(default=0)
    own_goals: Mapped[int] = mapped_column(default=0)
    penalties_missed: Mapped[int] = mapped_column(default=0)
    penalties_saved: Mapped[int] = mapped_column(default=0)
    bonus: Mapped[int] = mapped_column(default=0)
    total_points: Mapped[int] = mapped_column(default=0)

    xg: Mapped[float | None] = mapped_column(Float)
    xa: Mapped[float | None] = mapped_column(Float)
    npxg: Mapped[float | None] = mapped_column(Float)
    market_value: Mapped[float | None] = mapped_column(Float)
    composite_rating: Mapped[float | None] = mapped_column(Float)

    player: Mapped[Player] = relationship(back_populates="stats")
