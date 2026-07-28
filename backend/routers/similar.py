from fastapi import APIRouter, HTTPException, Depends, Query
from typing import AsyncGenerator
from asyncpg import Connection
from database import get_db_connection
from models import PlayerSummary, Club, League, Country, SimilarPlayer
from roles import broad_role, clean_position

router = APIRouter()

async def db_conn() -> AsyncGenerator[Connection, None]:
    async for conn in get_db_connection():
        yield conn

# -----------------------------------------------------------------------
# GET /api/players/{id}/similar
# Fetches the target player's vector, then finds the closest players by
# cosine distance — restricted to players who share at least one position
# (main OR alternate) with the target. Returns a similarity_score in
# [0, 1] (1 = identical) so the client can threshold.
# -----------------------------------------------------------------------
@router.get("/{player_id}/similar", response_model=list[SimilarPlayer])
async def get_similar_players(
    player_id: int,
    season: str = Query("2024/2025"),
    limit: int = Query(20, ge=1, le=100),
    conn: Connection = Depends(db_conn)
):
    target = await conn.fetchrow("""
        SELECT p.id, p.main_position, pss.stats_vector,
            COALESCE(ap.positions, ARRAY[]::text[]) AS alternate_positions
        FROM players p
        JOIN player_season_stats pss ON p.id = pss.player_id
        LEFT JOIN (
            SELECT player_id, ARRAY_AGG(position) AS positions
            FROM player_alternate_positions GROUP BY player_id
        ) ap ON ap.player_id = p.id
        WHERE p.id = $1 AND pss.season = $2
    """, player_id, season)

    if not target:
        raise HTTPException(status_code=404, detail="Player not found or no stats for the specified season.")

    vector = target['stats_vector']
    # Every role the target can fill — a candidate qualifies if it shares any of them.
    target_positions = list(target['alternate_positions'])
    if target['main_position']:
        target_positions.append(target['main_position'])
    target_positions = list(set(target_positions))

    rows = await conn.fetch("""
        SELECT p.id, p.name, p.main_position, p.photo_url,
            p.current_market_value_eur,
            DATE_PART('year', AGE(p.date_of_birth))::int AS age,
            COALESCE(ap.positions, ARRAY[]::text[]) AS alternate_positions,
            co.id AS country_id, co.name AS country_name, co.flag_url AS country_flag_url,
            cl.id AS club_id, cl.name AS club_name, cl.logo_url AS club_logo_url,
            l.id AS league_id, l.name AS league_name, l.logo_url AS league_logo_url,
            lco.id AS league_country_id, lco.name AS league_country_name, lco.flag_url AS league_country_flag_url,
            1 - (pss.stats_vector <=> $2::vector) AS similarity_score
        FROM players p
        JOIN player_season_stats pss ON p.id = pss.player_id
        LEFT JOIN countries co ON p.country_id = co.id
        LEFT JOIN clubs cl ON p.club_id = cl.id
        LEFT JOIN leagues l ON cl.league_id = l.id
        LEFT JOIN countries lco ON l.country_id = lco.id
        LEFT JOIN (
            SELECT player_id, ARRAY_AGG(position) AS positions
            FROM player_alternate_positions GROUP BY player_id
        ) ap ON ap.player_id = p.id
        WHERE pss.season = $1 AND p.id != $3 AND pss.stats_vector IS NOT NULL
            AND (
                p.main_position = ANY($4::text[])
                OR EXISTS (
                    SELECT 1 FROM player_alternate_positions pap
                    WHERE pap.player_id = p.id AND pap.position = ANY($4::text[])
                )
            )
        ORDER BY pss.stats_vector <=> $2::vector ASC
        LIMIT $5
    """, season, vector, player_id, target_positions, limit)

    return [
        SimilarPlayer(
            player=PlayerSummary(
                id=row['id'],
                name=row['name'],
                category=broad_role(row['main_position']),
                main_position=clean_position(row['main_position']),
                alternate_positions=list(row['alternate_positions']),
                age=row['age'],
                photo_url=row['photo_url'],
                current_market_value_eur=row['current_market_value_eur'],
                country=Country(id=row['country_id'], name=row['country_name'], flag_url=row['country_flag_url']) if row['country_name'] else None,
                club=Club(
                    id=row['club_id'],
                    name=row['club_name'],
                    logo_url=row['club_logo_url'],
                    league=League(
                        id=row['league_id'],
                        name=row['league_name'],
                        logo_url=row['league_logo_url'],
                        country=Country(
                            id=row['league_country_id'],
                            name=row['league_country_name'],
                            flag_url=row['league_country_flag_url']
                        ) if row['league_country_name'] else None
                    ) if row['league_name'] else None
                ) if row['club_name'] else None
            ),
            similarity_score=round(row['similarity_score'], 4)
        )
        for row in rows
    ]
