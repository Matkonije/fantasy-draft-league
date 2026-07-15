from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TradePropose(BaseModel):
    receiver_team_id: int
    players_from_proposer: list[int] = Field(min_length=1, max_length=3)
    players_from_receiver: list[int] = Field(min_length=1, max_length=3)


class TradeVoteIn(BaseModel):
    approve: bool


class TradeVoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    team_id: int
    approve: bool


class TradeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fantasy_league_id: int
    proposer_team_id: int
    receiver_team_id: int
    players_from_proposer: list[int]
    players_from_receiver: list[int]
    status: str
    fairness_ratio: float | None
    voting_deadline: datetime | None
    created_at: datetime
    resolved_at: datetime | None
    votes: list[TradeVoteOut] = []


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    message: str
    data: dict
    read: bool
    created_at: datetime


class MarkReadIn(BaseModel):
    ids: list[int] | None = None  # None = mark all read
