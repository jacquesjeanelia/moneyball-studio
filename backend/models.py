from pydantic import BaseModel
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

class PlayerSummary(BaseModel):
    id: int
    name: str
    country: Optional[Country] = None
    main_position: Optional[str] = None
    age: Optional[int] = None
    club: Optional[Club] = None
    photo_url: Optional[str] = None

class PlayerStats(BaseModel):
    id: int
    minutes_played: Optional[int] = None
    npxg_per90: Optional[float] = None
    xa_per90: Optional[float] = None
    shots_on_target_per90: Optional[float] = None
    progressive_passes_per90: Optional[float] = None
    successful_dribbles_per90: Optional[float] = None
    pass_completion_percentage: Optional[float] = None
    tackles_interceptions_per90: Optional[float] = None
    aerial_duels_won_percentage: Optional[float] = None
    ball_recoveries_per90: Optional[float] = None

class PlayerDetail(PlayerSummary):
    id: int
    name: str
    age: Optional[int] = None
    date_of_birth: Optional[str] = None
    main_position: Optional[str] = None
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