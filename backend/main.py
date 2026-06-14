from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import init_db_pool
from routers import players, similar

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db_pool()
    print("Database connection pool initialized.")
    yield

app = FastAPI(
    title="Moneyball API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(players.router, prefix="/api/players", tags=["players"])
app.include_router(similar.router, prefix="/api/similar", tags=["similarity"])
@app.get("/health")
async def health():
    return {"status": "ok"}