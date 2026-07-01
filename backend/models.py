from pydantic import BaseModel, Field
from typing import Optional

class Country(BaseModel):
    id: int
    name: str
    flag_url: Optional[str] = None

class League(BaseModel):
    id: int
    name: str
    country: Optional[Country] = None
    logo_url: Optional[str] = None

class Club(BaseModel):
    id: int
    name: str
    league: Optional[League] = None
    logo_url: Optional[str] = None

class PlayerStats(BaseModel):
    # The 12 headline metrics surfaced in the UI (radar + stat table), mapped
    # 1:1 to real player_season_stats columns. The 17-dim PCA stats_vector that
    # drives cosine similarity lives server-side only and is never sent here.
    id: int
    minutes_played: Optional[int] = None
    # Attacking
    npxg_per90: Optional[float] = None
    shots_on_target_per90: Optional[float] = None
    xa_per90: Optional[float] = None
    big_chances_created_per90: Optional[float] = None
    # Possession & progression
    successful_passes_per90: Optional[float] = None
    successful_pass_rate: Optional[float] = None
    successful_dribbles_per90: Optional[float] = None
    accurate_long_balls_per90: Optional[float] = None
    # Defending & duels
    tackles_per90: Optional[float] = None
    interceptions_per90: Optional[float] = None
    recoveries_per90: Optional[float] = None
    aerial_duel_success_rate: Optional[float] = None

class PlayerSummary(BaseModel):
    id: int
    name: str
    country: Optional[Country] = None
    # Broad role used for colour-coding / the All·Attackers·Midfielders·Defenders
    # segmented control. One of: "Attack", "Midfield", "Defender".
    category: Optional[str] = None
    # Specific role shown on cards/pills, e.g. "CM", "LW", "CB".
    main_position: Optional[str] = None
    # Other roles the player can fill (specific codes), used by the position filter.
    alternate_positions: list[str] = Field(default_factory=list)
    age: Optional[int] = None
    club: Optional[Club] = None
    photo_url: Optional[str] = None
    current_market_value_eur: Optional[int] = None
    season_stats: Optional[PlayerStats] = None

class PlayerDetail(PlayerSummary):
    id: int
    name: str
    age: Optional[int] = None
    date_of_birth: Optional[str] = None
    category: Optional[str] = None
    main_position: Optional[str] = None
    alternate_positions: list[str] = Field(default_factory=list)
    preferred_foot: Optional[str] = None
    height_cm: Optional[int] = None
    country: Optional[Country] = None
    club: Optional[Club] = None
    photo_url: Optional[str] = None
    current_market_value_eur: Optional[int] = None
    season_stats: Optional[PlayerStats] = None

class SimilarPlayer(BaseModel):
    player: PlayerSummary
    similarity_score: float