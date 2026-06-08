CREATE EXTENSION IF NOT EXISTS "vector";

CREATE TABLE IF NOT EXISTS "clubs" (
    "id" SERIAL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "logo_url" TEXT,
    "league" VARCHAR(100) 
);

CREATE TABLE IF NOT EXISTS "countries" (
    "id" SERIAL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "flag_url" TEXT
);

CREATE TABLE IF NOT EXISTS "players" (
    "id" SERIAL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "age" INT,
    "club_id" INT REFERENCES clubs(id),
    "country_id" INT REFERENCES countries(id) ON DELETE SET NULL,
    "photo_url" TEXT
);

CREATE TABLE IF NOT EXISTS "player_positions" (
    "player_id" INT,
    "position" VARCHAR(50) NOT NULL,
    PRIMARY KEY (player_id, position),
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "player_season_stats" (
    "player_id" INT,
    "season" VARCHAR(20) NOT NULL,
    "minutes_played" INT,
    "goals" INT,
    "assists" INT,
    "stats_vector" VECTOR(3),
    PRIMARY KEY (player_id, season),
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
);

CREATE INDEX ON player_season_stats USING hnsw (stats_vector vector_cosine_ops);

