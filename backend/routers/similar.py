from fastapi import APIRouter, HTTPException, Depends, Query
from typing import AsyncGenerator
from asyncpg import Connection
from database import get_db_connection
from models import PlayerSummary, PlayerDetail, Club, SimilarPlayer

router = APIRouter()

async def db_conn() -> AsyncGenerator[Connection, None]:
    async for conn in get_db_connection():
        yield conn

# -----------------------------------------------------------------------
# GET /api/players/{id}/similar
# Fetches the target player's vector, then finds the 5 closest
# players by cosine distance — filtered to the same position & season
# -----------------------------------------------------------------------
@router.get("/{player_id}/similar", response_model=list[SimilarPlayer])
async def get_similar_players(
    player_id: int,
    season: str = Query("2024/2025"),
    limit: int = Query(5, ge=1, le=20),
    conn: Connection = Depends(db_conn)
):
    target = await conn.fetchrow("""
        SELECT p.id, p.main_position, pss.stats_vector
        FROM players p
        JOIN player_season_stats pss ON p.id = pss.player_id
        WHERE p.id = $1 AND pss.season = $2
    """, player_id, season)

    if not target:
        raise HTTPException(status_code=404, detail="Player not found or no stats for the specified season.")
    
    position = target['main_position']
    vector = target['stats_vector']

    rows = await conn.fetch("""
        SELECT p.id, p.name, p.main_position, p.photo_url,
            DATE_PART('year', p.date_of_birth)::int AS age,
            cl.id AS club_id, cl.name AS club_name, cl.logo_url AS club_logo_url,
            1 - (pss.stats_vector <=> $2::vector) AS similarity_score
        FROM players p
        JOIN player_season_stats pss ON p.id = pss.player_id
        JOIN clubs cl ON p.club_id = cl.id
        WHERE pss.season = $1 AND p.id != $3 AND p.main_position = $4 AND pss.stats_vector IS NOT NULL
        ORDER BY pss.stats_vector <= $2::vector ASC
        LIMIT $5
    """, season, vector, player_id, position, limit)

    return [
        SimilarPlayer(
            player=PlayerSummary(
                id=row['id'],
                name=row['name'],
                main_position=row['main_position'],
                age=row['age'],
                photo_url=row['photo_url'],
                club=Club(
                    id=row['club_id'],
                    name=row['club_name'],
                    logo_url=row['club_logo_url']
                )
            ),
            similarity_score=round(row['similarity_score'], 4)
        )
        for row in rows
    ]
