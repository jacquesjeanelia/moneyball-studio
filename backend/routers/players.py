from fastapi import APIRouter, HTTPException, Depends, Query
from typing import AsyncGenerator
from asyncpg import Connection
from database import get_db_connection
from models import PlayerSummary, PlayerDetail, PlayerStats, Club, League, Country
from roles import broad_role, specific_role, role_categories, role_positions, clean_position

router = APIRouter()

async def db_conn() -> AsyncGenerator[Connection, None]:
    async for conn in get_db_connection():
        yield conn


# All 32 stat columns from player_season_stats, in canonical order, shared by
# every query that returns season stats. Aliased to a table in each query via
# {a} (e.g. "pss").
STAT_COLUMNS = (
    "minutes_played",
    # Attacking
    "npxg_per90", "npxg_percentile",
    "shots_per90", "shots_percentile",
    "shots_on_target_per90", "shots_on_target_percentile",
    "headed_shots_per90", "headed_shots_percentile",
    "xa_per90", "xa_percentile",
    "chances_created_per90", "chances_created_percentile",
    "big_chances_created_per90", "big_chances_created_percentile",
    "successful_crosses_per90", "successful_crosses_percentile",
    "successful_cross_rate", "successful_cross_rate_percentile",
    "opposition_box_touches_per90", "opposition_box_touches_percentile",
    # Possession & progression
    "successful_passes_per90", "successful_passes_percentile",
    "successful_pass_rate", "successful_pass_rate_percentile",
    "accurate_long_balls_per90", "accurate_long_balls_percentile",
    "accurate_long_balls_rate", "accurate_long_balls_rate_percentile",
    "successful_dribbles_per90", "successful_dribbles_percentile",
    "successful_dribble_rate", "successful_dribble_rate_percentile",
    "touches_per90", "touches_percentile",
    "dispossessed_per90", "dispossessed_percentile",
    "fouls_won_per90", "fouls_won_percentile",
    "duels_won_per90", "duels_won_percentile",
    "duel_success_rate", "duel_success_rate_percentile",
    # Defending & physical
    "aerial_duels_won_per90", "aerial_duels_won_percentile",
    "aerial_duel_success_rate", "aerial_duel_success_rate_percentile",
    "tackles_per90", "tackles_percentile",
    "interceptions_per90", "interceptions_percentile",
    "blocks_per90", "blocks_percentile",
    "clearances_per90", "clearances_percentile",
    "recoveries_per90", "recoveries_percentile",
    "possession_won_final_third_per90", "possession_won_final_third_percentile",
    "dribbled_past_per90", "dribbled_past_percentile",
    "fouls_committed_per90", "fouls_committed_percentile",
    "defcon_per90", "defcon_percentile",
)


def _stat_select(alias: str) -> str:
    """SQL fragment selecting every stat column off `alias`, plus the presence flag."""
    cols = ", ".join(f"{alias}.{c}" for c in STAT_COLUMNS)
    return f"{alias}.player_id AS stats_player_id, {cols}"


def _build_stats(row) -> PlayerStats | None:
    """Build a PlayerStats from a row, or None if the player has no stats row."""
    if row["stats_player_id"] is None:
        return None
    return PlayerStats(id=row["id"], **{c: row[c] for c in STAT_COLUMNS})


# ---------------------------------------------------------------------------------
# GET /api/players
# Returns a list of players, optionally filtered by season, position, club, country.
# Each row carries market value + season stats so the client can do instant
# search / filtering / percentile radars without N round-trips.
# ---------------------------------------------------------------------------------
@router.get("/", response_model=list[PlayerSummary])
async def list_players(
    season: str = Query("2024/2025", description="Season to filter stats by"),
    category: str | None = Query(None, description="Attack, Midfield, Defender"),
    country_id: int | None = Query(None),
    club_id: int | None = Query(None),
    conn: Connection = Depends(db_conn)
):
    filters = ["pss.season = $1"]
    args = [season]
    idx = 2

    if category:
        # `category` is a broad role (Attack/Midfield/Defender). The dataset
        # stores specific labels, so match the label set for the role, falling
        # back to the position code when the label is missing/unrecognised.
        labels = role_categories(category)
        codes = role_positions(category)
        filters.append(
            f"(LOWER(p.category) = ANY(${idx}::text[])"
            f" OR (p.category IS NULL AND UPPER(p.main_position) = ANY(${idx + 1}::text[])))"
        )
        args.append(labels)
        args.append(codes)
        idx += 2

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
            p.id, p.name, p.category, p.main_position, p.photo_url, p.country_id,
            p.current_market_value_eur,
            DATE_PART('year', AGE(p.date_of_birth)) AS age,
            COALESCE(ap.positions, ARRAY[]::text[]) AS alternate_positions,
            co.name AS country_name, co.flag_url AS country_flag_url,
            p.club_id, cl.name AS club_name, cl.logo_url AS club_logo_url,
            l.id AS league_id, l.name AS league_name, l.logo_url AS league_logo_url, l.country_id AS league_country_id,
            lco.name AS league_country_name, lco.flag_url AS league_country_flag_url,
            {_stat_select('pss')}
        FROM players p
        LEFT JOIN countries co ON p.country_id = co.id
        LEFT JOIN clubs cl ON p.club_id = cl.id
        LEFT JOIN leagues l ON cl.league_id = l.id
        LEFT JOIN countries lco ON l.country_id = lco.id
        LEFT JOIN player_season_stats pss ON p.id = pss.player_id
        LEFT JOIN (
            SELECT player_id, ARRAY_AGG(position ORDER BY position) AS positions
            FROM player_alternate_positions GROUP BY player_id
        ) ap ON ap.player_id = p.id
        WHERE {where}
        ORDER BY p.name ASC
    """, *args)

    return [
        PlayerSummary(
            id=row["id"],
            name=row["name"],
            country=Country(id=row["country_id"], name=row["country_name"], flag_url=row["country_flag_url"]) if row["country_name"] else None,
            category=broad_role(row["category"], row["main_position"]),
            role=specific_role(row["main_position"]),
            main_position=clean_position(row["main_position"]),
            alternate_positions=list(row["alternate_positions"]),
            age=int(row["age"]) if row["age"] else None,
            current_market_value_eur=row["current_market_value_eur"],
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
            season_stats=_build_stats(row),
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
    row = await conn.fetchrow(f"""
        SELECT
            p.id, p.name, p.category, p.main_position, p.photo_url,
            DATE_PART('year', AGE(p.date_of_birth)) AS age,
            p.date_of_birth, p.preferred_foot, p.height_cm, p.current_market_value_eur,
            COALESCE(ap.positions, ARRAY[]::text[]) AS alternate_positions,
            p.country_id, co.name AS country_name, co.flag_url AS country_flag_url,
            p.club_id, cl.name AS club_name, cl.logo_url AS club_logo_url,
            l.id AS league_id, l.name AS league_name, l.logo_url AS league_logo_url, l.country_id AS league_country_id,
            lco.name AS league_country_name, lco.flag_url AS league_country_flag_url,
            {_stat_select('ps')}
        FROM players p
        LEFT JOIN countries co ON p.country_id = co.id
        LEFT JOIN clubs cl ON p.club_id = cl.id
        LEFT JOIN leagues l ON cl.league_id = l.id
        LEFT JOIN countries lco ON l.country_id = lco.id
        LEFT JOIN player_season_stats ps ON p.id = ps.player_id AND ps.season = $2
        LEFT JOIN (
            SELECT player_id, ARRAY_AGG(position ORDER BY position) AS positions
            FROM player_alternate_positions GROUP BY player_id
        ) ap ON ap.player_id = p.id
        WHERE p.id = $1
    """, player_id, season)

    if not row:
        raise HTTPException(status_code=404, detail="Player not found")

    return PlayerDetail(
        id=row["id"],
        name=row["name"],
        age=int(row["age"]) if row["age"] else None,
        category=broad_role(row["category"], row["main_position"]),
        role=specific_role(row["main_position"]),
        main_position=clean_position(row["main_position"]),
        alternate_positions=list(row["alternate_positions"]),
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
        season_stats=_build_stats(row),
    )