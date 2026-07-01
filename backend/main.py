import os
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

# Comma-separated list of allowed origins, e.g.
#   CORS_ORIGINS="http://localhost:5173,https://moneyball.vercel.app"
# Defaults to the local Vite dev server.
_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:4173")
allow_origins = [o.strip() for o in _origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(players.router, prefix="/api/players", tags=["players"])
# Mounted under /api/players so the route resolves to
# GET /api/players/{id}/similar
app.include_router(similar.router, prefix="/api/players", tags=["similarity"])

@app.get("/health")
async def health():
    return {"status": "ok"}
