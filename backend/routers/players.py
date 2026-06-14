from fastapi import APIRouter, HTTPException, Depends, Query
from typing import AsyncGenerator
from asyncpg import Connection
from database import get_db_connection
from models import PlayerSummary, PlayerDetail, PlayerStats, Club, League, Country

router = APIRouter()

async def db_conn() -> AsyncGenerator[Connection, None]:
    async for conn in get_db_connection():
        yield conn


# ---------------------------------------------------------------------------------
# GET /api/players
# Returns a list of players, optionally filtered by season, position, club, country
# ---------------------------------------------------------------------------------
@router.get("/", response_model=list[PlayerSummary])
async def list_players(
    season: str = Query("2024/2025", description="Season to filter stats by"),
    position: str | None = Query(None, description="Attack, Midfield, Defender"),
    country_id: int | None = Query(None),
    club_id: int | None = Query(None),
    conn: Connection = Depends(db_conn)
):
    filters = ["pss.season = $1"]
    args = [season]
    idx = 2

    if position:
        filters.append(f"p.main_position = ${idx}")
        args.append(position)
        idx += 1
    
    if country_id:
        filters.append(f"co.id = ${idx}")
        args.append(country_id)
        idx += 1

    if club_id:
        filters.append(f"cl.id = ${idx}")
        args.append(club_id)
        idx += 1

    where = " AND ".join(filters)

    rows = await conn.fetch(f"""
        SELECT 
            p.id, p.name, p.main_position, p.photo_url, p.country_id, 
            DATE_PART('year', AGE(p.date_of_birth)) AS age,
            co.name AS country_name, co.flag_url AS country_flag_url,
            p.club_id, cl.name AS club_name, cl.logo_url AS club_logo_url,
            l.id AS league_id, l.name AS league_name, l.logo_url AS league_logo_url, l.country_id AS league_country_id,
            lco.name AS league_country_name, lco.flag_url AS league_country_flag_url
        FROM players p
        LEFT JOIN countries co ON p.country_id = co.id
        LEFT JOIN clubs cl ON p.club_id = cl.id
        LEFT JOIN leagues l ON cl.league_id = l.id
        LEFT JOIN countries lco ON l.country_id = lco.id
        LEFT JOIN player_season_stats pss ON p.id = pss.player_id
        WHERE {where}
        ORDER BY p.name ASC
    """, *args)

    return [
        PlayerSummary(
            id=row["id"],
            name=row["name"],
            country=Country(id=row["country_id"], name=row["country_name"], flag_url=row["country_flag_url"]) if row["country_name"] else None,
            main_position=row["main_position"],
            age=int(row["age"]) if row["age"] else None,
            club=Club(
                id=row["club_id"],
                name=row["club_name"],
                logo_url=row["club_logo_url"],
                league=League(
                    id=row["league_id"], 
                    name=row["league_name"], 
                    logo_url=row["league_logo_url"], 
                    country=Country(
                        id=row["league_country_id"], 
                        name=row["league_country_name"], 
                        flag_url=row["league_country_flag_url"]
                    )
                ) if row["league_name"] else None
            ) if row["club_name"] else None,
            photo_url=row["photo_url"]
        ) for row in rows
    ]

# -----------------------------------------------------------------------
# GET /api/players/{id}
# Returns full detail for one player including their stats
# -----------------------------------------------------------------------

@router.get("/{player_id}", response_model=PlayerDetail)
async def get_player(
    player_id: int,
    season: str = Query("2024/2025"),
    conn: Connection = Depends(db_conn)
):
    row = await conn.fetchrow("""
        SELECT 
            p.id, p.name, p.main_position, p.photo_url,
            DATE_PART('year', AGE(p.date_of_birth)) AS age,
            p.date_of_birth, p.preferred_foot, p.height_cm, p.current_market_value_eur,
            p.country_id, co.name AS country_name, co.flag_url AS country_flag_url,
            p.club_id, cl.name AS club_name, cl.logo_url AS club_logo_url,
            l.id AS league_id, l.name AS league_name, l.logo_url AS league_logo_url, l.country_id AS league_country_id,
            lco.name AS league_country_name, lco.flag_url AS league_country_flag_url,
            ps.player_id AS stats_player_id, ps.minutes_played, ps.npxg_per90, ps.xa_per90,
            ps.shots_on_target_per90, ps.progressive_passes_per90,
            ps.successful_dribbles_per90, ps.pass_completion_percentage,
            ps.tackles_interceptions_per90, ps.aerial_duels_won_percentage,
            ps.ball_recoveries_per90
        FROM players p
        LEFT JOIN countries co ON p.country_id = co.id
        LEFT JOIN clubs cl ON p.club_id = cl.id
        LEFT JOIN leagues l ON cl.league_id = l.id
        LEFT JOIN countries lco ON l.country_id = lco.id
        LEFT JOIN player_season_stats ps ON p.id = ps.player_id AND ps.season = $2
        WHERE p.id = $1
    """, player_id, season)

    if not row:
        raise HTTPException(status_code=404, detail="Player not found")

    return PlayerDetail(
        id=row["id"],
        name=row["name"],
        age=int(row["age"]) if row["age"] else None,
        main_position=row["main_position"],
        preferred_foot=row["preferred_foot"],
        height_cm=row["height_cm"],
        country=Country(id=row["country_id"], name=row["country_name"], flag_url=row["country_flag_url"]) if row["country_name"] else None,
        club=Club(
            id=row["club_id"],
            name=row["club_name"],
            logo_url=row["club_logo_url"],
            league=League(
                id=row["league_id"], 
                name=row["league_name"], 
                logo_url=row["league_logo_url"], 
                country=Country(
                    id=row["league_country_id"], 
                    name=row["league_country_name"], 
                    flag_url=row["league_country_flag_url"]
                )
            ) if row["league_name"] else None
        ) if row["club_name"] else None,
        photo_url=row["photo_url"],
        current_market_value_eur=row["current_market_value_eur"],
        date_of_birth=str(row["date_of_birth"]) if row["date_of_birth"] else None,
        season_stats=PlayerStats(
            id=row["id"],
            minutes_played=row["minutes_played"],
            npxg_per90=row["npxg_per90"],
            xa_per90=row["xa_per90"],
            shots_on_target_per90=row["shots_on_target_per90"],
            progressive_passes_per90=row["progressive_passes_per90"],
            successful_dribbles_per90=row["successful_dribbles_per90"],
            pass_completion_percentage=row["pass_completion_percentage"],
            tackles_interceptions_per90=row["tackles_interceptions_per90"],
            aerial_duels_won_percentage=row["aerial_duels_won_percentage"],
            ball_recoveries_per90=row["ball_recoveries_per90"]
        ) if row["stats_player_id"] is not None else None
    )