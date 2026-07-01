import os
import asyncpg
from pgvector.asyncpg import register_vector

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/football",
)

pool: asyncpg.Pool | None = None


async def init_db_pool() -> None:
    global pool
    pool = await asyncpg.create_pool(
        dsn=DB_URL,
        init=register_vector,
        min_size=2,
        max_size=10,
    )


async def get_db_connection():
    async with pool.acquire() as conn:  # type: ignore[union-attr]
        yield conn
