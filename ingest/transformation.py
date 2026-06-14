import os
import ast
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import psycopg2
from psycopg2.extras import execute_values

DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     int(os.getenv("DB_PORT", "5432")),
    "dbname":   os.getenv("DB_NAME",     "football"),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}

RAW_DATA_PATH = "data/raw/combined_player_dataset.csv"
PROCESSED_DATA_PATH = "data/processed/combined_player_dataset_processed.csv"
COUNTRIES_PATH = "data/raw/countries_data.csv"
LEAGUES_PATH = "data/raw/leagues_data.csv"
CLUBS_PATH = "data/raw/club_data.csv"

FEATURE_COLS = [
    'npxg_per90', 'xa_per90', 'shots_on_target_per90', 
    'progressive_passes_per90', 'successful_dribbles_per90', 
    'pass_completion_percentage', 'tackles_interceptions_per90', 
    'aerial_duels_won_percentage','ball_recoveries_per90', 'fouls_committed_per90'
]

def load_and_clean_data():
    if not os.path.exists(RAW_DATA_PATH):
        raise FileNotFoundError(f"Raw data file not found at {RAW_DATA_PATH}. Please run the ingestion script first.")
    df = pd.read_csv(RAW_DATA_PATH)
    df = df[df['minutes_played'] >= 450]
    df = df[df['player_name'].notnull()]
    df[FEATURE_COLS] = df[FEATURE_COLS].fillna(0)
    df = df[df['transfermarkt_position'] != 'Goalkeeper']
    df['transfermarkt_position'] = df['transfermarkt_position'].fillna('Unknown')
    return df

def scale_features(df):
    scaler = MinMaxScaler()
    scaled_features = scaler.fit_transform(df[FEATURE_COLS])

    df['stats_vector'] = [str(list(vector.tolist())) for vector in scaled_features]

    os.makedirs(os.path.dirname(PROCESSED_DATA_PATH), exist_ok=True)
    df.to_csv(PROCESSED_DATA_PATH, index=False, encoding='utf-8')
    print(f"Processed data saved to {PROCESSED_DATA_PATH}")
    return df

def _connect_db():
    return psycopg2.connect(**DB_CONFIG)

def _float(row, col:str):
    value = row[col]
    return None if value is None or (isinstance(value, float) and np.isnan(value)) else float(value)

def insert_countries(cur, countries_csv: str) -> dict[str, int]:
    if not os.path.exists(countries_csv):
        raise FileNotFoundError(f"Countries data file not found at {countries_csv}. Please ensure it exists.")
    
    df = pd.read_csv(countries_csv).fillna('')
    rows = [(df['country'], df['flag']) for _, df in df.iterrows()]

    execute_values(
        cur,
        """
            INSERT INTO countries (name, flag_url) 
            VALUES %s
            ON CONFLICT DO NOTHING
        """,
        rows
    )

    cur.execute("SELECT id, name FROM countries")
    return {name: id for id, name in cur.fetchall()}


def insert_leagues(cur, leagues_csv: str, country_id_map: dict[str, int]) -> dict[str, int]:
    if not os.path.exists(leagues_csv):
        raise FileNotFoundError(f"Leagues data file not found at {leagues_csv}. Please ensure it exists.")
    
    df = pd.read_csv(leagues_csv).fillna('')
    rows =  [(row['league'], country_id_map.get(row['country'], None), row['league_url']) for _, row in df.iterrows()]
    execute_values(
        cur,
        """
            INSERT INTO leagues (name, country_id, logo_url) 
            VALUES %s
            ON CONFLICT DO NOTHING
        """,
        rows
    )
    cur.execute("SELECT id, name FROM leagues")
    return {name: id for id, name in cur.fetchall()}


def insert_clubs(cur, clubs_csv: str, league_id_map: dict[str, int]) -> dict[str, int]:
    if not os.path.exists(clubs_csv):
        raise FileNotFoundError(f"Clubs data file not found at {clubs_csv}. Please ensure it exists.")
    
    df = pd.read_csv(clubs_csv).fillna('')
    rows = [(row['Club Name'], league_id_map.get(row['League'], None), row['Club Image URL']) for _, row in df.iterrows()]
    execute_values(
        cur,
        """
            INSERT INTO clubs (name, league_id, logo_url) 
            VALUES %s
            ON CONFLICT DO NOTHING
        """,
        rows
    )
    cur.execute("SELECT id, name FROM clubs")
    return {name: id for id, name in cur.fetchall()}


def insert_players(cur, df: pd.DataFrame, club_id_map: dict[str, int], country_id_map: dict[str, int]) -> dict[str, int]:
    rows = []
    df['date_of_birth'] = pd.to_datetime(df['date_of_birth'], dayfirst=True).dt.date
    for _, row in df.iterrows():
        country_id = country_id_map.get(row['country_of_citizenship'], None)
        club_id = club_id_map.get(row['club'], None)

        dob = row['date_of_birth'] if pd.notna(row['date_of_birth']) else None
        value = int(row['market_value_in_eur']) if pd.notna(row['market_value_in_eur']) else 0
        height = int(row['height_in_cm']) if pd.notna(row['height_in_cm']) else None

        rows.append((
            row['player_name'], 
            dob, 
            row['transfermarkt_position'], 
            row['preferred_foot'],
            height,
            club_id,
            country_id, 
            row['player_photo_url'], 
            value
        ))

    execute_values(
        cur,
        """
            INSERT INTO players (
                name, date_of_birth, main_position, preferred_foot, height_cm, club_id, country_id, photo_url, current_market_value_eur
            ) VALUES %s
            ON CONFLICT DO NOTHING
        """,
        rows
    )
    cur.execute("SELECT id, name FROM players")
    return {name: id for id, name in cur.fetchall()}

#TODO: insert_player_positions()

def insert_player_season_stats(cur, df: pd.DataFrame, player_id_map: dict[str, int]):
    rows = []
    for _, row in df.iterrows():
        player_id = player_id_map.get(row['player_name'], None)
        if player_id is None:
            continue

        vec = row['stats_vector']
        if vec is None or vec == 'None':
            continue
        if isinstance(vec, str):
            vec = ast.literal_eval(vec)
        
        vec_string ='[' + ','.join(f"{v:.8f}" for v in vec) + ']'

        rows.append((
            player_id, '2024/2025', _float(row, 'npxg_per90'), _float(row, 'xa_per90'), _float(row, 'shots_on_target_per90'), 
            _float(row, 'progressive_passes_per90'), _float(row, 'successful_dribbles_per90'), 
            _float(row, 'pass_completion_percentage'), _float(row, 'tackles_interceptions_per90'), 
            _float(row, 'aerial_duels_won_percentage'), _float(row, 'ball_recoveries_per90'), 
            _float(row, 'fouls_committed_per90'), vec_string
        ))

    execute_values(
        cur,
        """
            INSERT INTO player_season_stats (
                player_id, season, npxg_per90, xa_per90, shots_on_target_per90, 
                progressive_passes_per90, successful_dribbles_per90, pass_completion_percentage, 
                tackles_interceptions_per90, aerial_duels_won_percentage, ball_recoveries_per90, 
                fouls_committed_per90, stats_vector
            ) VALUES %s
            ON CONFLICT DO NOTHING
        """,
        rows
    )

def run():
    print("=" * 60)
    print("Phase 3 — Transform & Load")
    print("=" * 60)
 
    # --- Transform ---
    print("\n[1/2] Cleaning & vectorising…")
    df = load_and_clean_data()
    df = scale_features(df)
 
    # --- Load ---
    print("\n[2/2] Inserting into PostgreSQL…")
    conn = _connect_db()
    conn.autocommit = False
    cur = conn.cursor()
 
    try: 
        print("  → countries")
        country_id_map = insert_countries(cur, COUNTRIES_PATH)
        print(f"     {len(country_id_map)} countries")

        print("\n  → leagues")
        league_id_map = insert_leagues(cur, LEAGUES_PATH, country_id_map)
        print(f"     {len(league_id_map)} leagues")
 
        print("  → clubs")
        club_id_map = insert_clubs(cur, CLUBS_PATH, league_id_map)
        print(f"     {len(club_id_map)} clubs")
 
        print("  → players")
        player_id_map = insert_players(cur, df, club_id_map, country_id_map)
        print(f"     {len(player_id_map)} players")
 
        # print("  → player_positions")
        # insert_player_positions(cur, df, player_id_map)
 
        print("  → player_season_stats")
        insert_player_season_stats(cur, df, player_id_map)
 
        conn.commit()
        print("\n✓ All data committed successfully.")
 
    except Exception as exc:
        conn.rollback()
        print(f"\n✗ Error — transaction rolled back.\n  {exc}")
        raise
 
    finally:
        cur.close()
        conn.close()
 
 
if __name__ == "__main__":
    run()
 