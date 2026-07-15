from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(primary_key=True)
    fantasy_league_id: Mapped[int] = mapped_column(ForeignKey("fantasy_leagues.id"), index=True)
    draft_id: Mapped[int] = mapped_column(ForeignKey("drafts.id"))  # period anchor
    proposer_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    receiver_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    players_from_proposer: Mapped[list] = mapped_column(JSON)
    players_from_receiver: Mapped[list] = mapped_column(JSON)
    # proposed / voting / completed / rejected / cancelled
    status: Mapped[str] = mapped_column(String(20), default="proposed", index=True)
    fairness_ratio: Mapped[float | None] = mapped_column(Float)
    voting_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    votes: Mapped[list["TradeVote"]] = relationship(back_populates="trade")


class TradeVote(Base):
    __tablename__ = "trade_votes"
    __table_args__ = (UniqueConstraint("trade_id", "team_id", name="uq_trade_vote_team"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    trade_id: Mapped[int] = mapped_column(ForeignKey("trades.id"), index=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    approve: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    trade: Mapped[Trade] = relationship(back_populates="votes")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(40))
    message: Mapped[str] = mapped_column(String(500))
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    read: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
