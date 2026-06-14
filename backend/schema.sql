CREATE EXTENSION IF NOT EXISTS "vector";

CREATE TABLE IF NOT EXISTS "countries" (
    "id"       SERIAL PRIMARY KEY,
    "name"     VARCHAR(255) NOT NULL,
    "flag_url" TEXT
);

CREATE TABLE IF NOT EXISTS "leagues" (
    "id"       SERIAL PRIMARY KEY,
    "name"     VARCHAR(255) NOT NULL,
    "country_id"  INT REFERENCES countries(id) ON DELETE SET NULL,
    "logo_url" TEXT
);

CREATE TABLE IF NOT EXISTS "clubs" (
    "id"        SERIAL PRIMARY KEY,
    "name"      VARCHAR(255) NOT NULL,
    "logo_url"  TEXT,
    "league_id" INT REFERENCES leagues(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS "players" (
    "id"                     SERIAL PRIMARY KEY,
    "name"                   VARCHAR(255) NOT NULL,
    "date_of_birth"          DATE,
    "main_position"          VARCHAR(50),
    "preferred_foot"         VARCHAR(10),
    "height_cm"              INT,
    "club_id"                INT REFERENCES clubs(id)     ON DELETE SET NULL,
    "country_id"             INT REFERENCES countries(id) ON DELETE SET NULL,
    "photo_url"              TEXT,
    "current_market_value_eur" INT
);

CREATE TABLE IF NOT EXISTS "player_positions" (
    "player_id" INT,
    "position"  VARCHAR(50) NOT NULL,
    PRIMARY KEY (player_id, position),
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "player_season_stats" (
    "player_id"                    INT,
    "season"                       VARCHAR(20) NOT NULL,
    "minutes_played"               INT,
    "npxg_per90"                   FLOAT,
    "xa_per90"                     FLOAT,
    "shots_on_target_per90"        FLOAT,
    "progressive_passes_per90"     FLOAT,
    "successful_dribbles_per90"    FLOAT,
    "pass_completion_percentage"   FLOAT,
    "tackles_interceptions_per90"  FLOAT,
    "aerial_duels_won_percentage"  FLOAT,
    "ball_recoveries_per90"        FLOAT,
    "fouls_committed_per90"        FLOAT,
    "stats_vector"                 VECTOR(10),
    PRIMARY KEY (player_id, season),
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
);


CREATE INDEX ON player_season_stats USING hnsw (stats_vector vector_cosine_ops);