from pydantic import BaseModel, ConfigDict


class LeagueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    is_active: bool


class PlayerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    league_id: int
    name: str
    club: str
    position: str
    status: str
    price: float | None
    total_points: int
    fpl_id: int | None


class PlayerStatsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    gameweek: int
    minutes: int
    goals: int
    assists: int
    clean_sheets: int
    goals_conceded: int
    yellow_cards: int
    red_cards: int
    saves: int
    own_goals: int
    penalties_missed: int
    penalties_saved: int
    bonus: int
    total_points: int
    xg: float | None
    xa: float | None


class PlayerDetailOut(PlayerOut):
    stats: list[PlayerStatsOut]


class PlayerListOut(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[PlayerOut]
