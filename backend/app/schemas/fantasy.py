from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.player import PlayerOut


class FantasyLeagueCreate(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    league_id: int
    team_name: str = Field(min_length=2, max_length=100)
    pick_timer_seconds: int = Field(90, ge=10, le=600)


class FantasyLeagueJoin(BaseModel):
    invite_code: str
    team_name: str = Field(min_length=2, max_length=100)


class TeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fantasy_league_id: int
    user_id: int
    name: str


class FantasyLeagueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    league_id: int
    invite_code: str
    commissioner_id: int
    pick_timer_seconds: int
    teams: list[TeamOut] = []


class DraftPickOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pick_number: int
    round: int
    team_id: int
    player_id: int
    is_auto: bool


class PickRequest(BaseModel):
    player_id: int


class DraftStateOut(BaseModel):
    id: int
    fantasy_league_id: int
    status: str
    rounds: int
    draft_order: list[int]
    current_pick_index: int
    current_team_id: int | None
    current_pick_deadline: datetime | None
    server_time: datetime
    picks: list[DraftPickOut]


class RosterOut(BaseModel):
    team: TeamOut
    players: list[PlayerOut]
