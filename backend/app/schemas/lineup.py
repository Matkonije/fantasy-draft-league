from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LineupSlotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    player_id: int
    role: str
    bench_order: int
    is_captain: bool
    is_vice: bool


class LineupSet(BaseModel):
    gameweek: int = Field(ge=1, le=38)
    starters: list[int] = Field(min_length=11, max_length=11)
    bench: list[int] = Field(min_length=4, max_length=4, description="bench order; GK anywhere")
    captain_id: int
    vice_id: int


class LineupOut(BaseModel):
    team_id: int
    gameweek: int
    slots: list[LineupSlotOut]


class StandingRow(BaseModel):
    rank: int
    team_id: int
    team_name: str
    username: str
    total_points: int
    gameweeks_scored: int


class StandingsOut(BaseModel):
    fantasy_league_id: int
    standings: list[StandingRow]


class TeamScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    team_id: int
    gameweek: int
    points: int
    breakdown: dict
    computed_at: datetime


class GameweekOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    number: int
    deadline: datetime | None
    finished: bool
