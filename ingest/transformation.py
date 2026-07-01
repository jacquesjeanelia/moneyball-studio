from operator import pos
import os
import ast
import pprint
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import psycopg2
from psycopg2.extras import execute_values
import csv

def safe_read_csv(file_path, **kwargs):
    try:
        return pd.read_csv(file_path, encoding='utf-8', **kwargs)
    except UnicodeDecodeError:
        return pd.read_csv(file_path, encoding='latin1', **kwargs)


DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     int(os.getenv("DB_PORT", "5432")),
    "dbname":   os.getenv("DB_NAME",     "football"),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}

PLAYER_INFO_PATH = "data/raw/fotmob_players_info.csv"
PLAYER_STATS_PATH = "data/raw/fotmob_players_stats.csv"
COUNTRIES_PATH = "data/raw/countries_data.csv"
LEAGUES_PATH = "data/raw/fotmob_leagues.csv"
CLUBS_PATH = "data/raw/fotmob_clubs.csv"
PROCESSED_DATA_PATH = "data/processed/combined_player_dataset.csv"

PLAYER_IMAGE_URL = "https://images.fotmob.com/image_resources/playerimages/" # add {player_id}.png to get the image
CLUB_IMAGE_URL = "https://images.fotmob.com/image_resources/logo/teamlogo/" # add {club_id}.png to get the image
LEAGUE_IMAGE_URL = "https://images.fotmob.com/image_resources/logo/leaguelogo/" # add {league_id}.png to get the image

FEATURE_COLS = [
    'npxg_per_90', 'shots_per_90', 'sot_per_90', 
    'headed_shots_per_90', 'xa_per_90', 'succ_pass_per_90', 
    'succ_pass_rate', 'acc_long_balls_per_90', 'succ_long_balls_rate', 
    'chances_created_per_90', 'big_chances_created_per_90', 
    'succ_crosses_per_90', 'succ_crosses_rate', 'succ_dribbles_per_90', 
    'succ_dribbles_rate', 'duels_won_per_90', 'duels_won_rate', 
    'aerials_won_per_90', 'aerials_won_rate', 'touches_per_90', 
    'touches_opp_box_per_90', 'dispossessed_per_90', 'fouls_won_per_90', 
    'defcon_per_90', 'tackles_per_90', 'interceptions_per_90', 
    'blocks_per_90', 'fouls_committed_per_90', 'recoveries_per_90', 
    'poss_won_final_3rd_per_90', 'succ_dribbles_def_per_90', 'clearances_per_90'
]

def merge_player_data():
    if not os.path.exists(PLAYER_INFO_PATH):
        raise FileNotFoundError(f"Player info file not found at {PLAYER_INFO_PATH}. Please run the ingestion script first.")
    if not os.path.exists(PLAYER_STATS_PATH):
        raise FileNotFoundError(f"Player stats file not found at {PLAYER_STATS_PATH}. Please run the ingestion script first.")

    df_info = safe_read_csv(PLAYER_INFO_PATH)
    df_stats = safe_read_csv(PLAYER_STATS_PATH)

    # Merge dataframes on player_id
    df_merged = pd.merge(df_info, df_stats, left_on='fotmob_id', right_on='player_id', how='inner')
    return df_merged

def load_and_clean_data():
    df = merge_player_data()
    # df = df[df['minutes_played'] >= 450]
    df = df[df['name'].notnull()]
    df[FEATURE_COLS] = df[FEATURE_COLS].fillna(0)
    df['dob'] = df['dob'].str.slice(0, 10)
    df = df[df['category'].str.lower() != 'keeper']
    df = df[~df['positions'].str.contains('GK', na=False)]
    # df.to_csv("data/processed/cleaned_player_dataset.csv", index=False, encoding='utf-8')
    return df

def scale_features(df):
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(df[FEATURE_COLS])

    pca = PCA(n_components=17)
    pca_stats = pca.fit_transform(scaled_features)

    df['stats_vector'] = [str(list(vector.tolist())) for vector in pca_stats]

    os.makedirs(os.path.dirname("data/processed/processed_player_dataset.csv"), exist_ok=True)
    df.to_csv("data/processed/processed_player_dataset.csv", index=False, encoding='utf-8')
    print(f"Processed data saved to {"data/processed/processed_player_dataset.csv"}")
    return df

def _connect_db():
    return psycopg2.connect(**DB_CONFIG)

def _float(row, col:str):
    value = row[col]
    return None if value is None or (isinstance(value, float) and np.isnan(value)) else float(value)

def insert_countries(cur) -> dict[str, int]:
    if not os.path.exists(COUNTRIES_PATH):
        raise FileNotFoundError(f"Countries data file not found at {COUNTRIES_PATH}. Please ensure it exists.")
    
    df = safe_read_csv(COUNTRIES_PATH).fillna('')
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


def insert_leagues(cur, country_id_map: dict[str, int]) -> dict[int, int]:
    if not os.path.exists(LEAGUES_PATH):
        raise FileNotFoundError(f"Leagues data file not found at {LEAGUES_PATH}. Please ensure it exists.")
    
    df = safe_read_csv(LEAGUES_PATH).fillna('')
    rows =  [(row['league'], country_id_map.get(row['country'], None), LEAGUE_IMAGE_URL + f"{row['league_id']}.png") for _, row in df.iterrows()]
    fotmob_map = {row['league_id']: row['league'] for _, row in df.iterrows()}
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
    db_map = {name: id for id, name in cur.fetchall()}
    out_map = {k: db_map[v] for k, v in fotmob_map.items() if v in db_map} #fotmob_id -> db_id
    return out_map


def insert_clubs(cur, league_id_map: dict[int, int]) -> dict[int, int]:
    if not os.path.exists(CLUBS_PATH):
        raise FileNotFoundError(f"Clubs data file not found at {CLUBS_PATH}. Please ensure it exists.")
    
    print(league_id_map)
    
    df = safe_read_csv(CLUBS_PATH).fillna('')
    fotmob_map = {int(row['team_id']): row['team_name'] for _, row in df.iterrows()}
    rows = [(row['team_name'], league_id_map.get(row['league_id'], None), CLUB_IMAGE_URL + f"{row['team_id']}.png") for _, row in df.iterrows()]
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
    db_map = {name: id for id, name in cur.fetchall()}
    out_map = {k: db_map[v] for k, v in fotmob_map.items() if v in db_map} # fotmob_id -> db_id
    return out_map


def insert_players(cur, df: pd.DataFrame, club_id_map: dict[str, int], country_id_map: dict[str, int]) -> dict[str, int]:
    rows = []
    df['dob'] = df['dob'].astype(str).str.strip()
    df['dob'] = pd.to_datetime(df['dob'], dayfirst=True, format='mixed', errors='coerce').dt.date
    for _, row in df.iterrows():
        country_id = country_id_map.get(row['country'], None)
        club_id = club_id_map.get(row['club_id'], None)
        name = row['name'] if pd.notna(row['name']) else None
        dob = row['dob'] if pd.notna(row['dob']) else None
        value = int(row['value']) if pd.notna(row['value']) else 0
        height = int(row['height_cm']) if pd.notna(row['height_cm']) else None
        category = row['category'] if pd.notna(row['category']) else None
        main_position = row['positions'].split(",")[0].strip() if pd.notna(row['positions']) else []
        foot = row['preferred_foot'] if pd.notna(row['preferred_foot']) else None
        photo_url = PLAYER_IMAGE_URL + f"{row['fotmob_id']}.png" if pd.notna(row['fotmob_id']) else None

        rows.append((
            name,
            dob,
            category,
            main_position,
            foot,
            height,
            club_id,
            country_id, 
            photo_url, 
            value
        ))

    execute_values(
        cur,
        """
            INSERT INTO players (
                name, date_of_birth, category, main_position, preferred_foot, height_cm, club_id, country_id, photo_url, current_market_value_eur
            ) VALUES %s
            ON CONFLICT DO NOTHING
        """,
        rows
    )
    cur.execute("SELECT id, name FROM players")
    return {name: id for id, name in cur.fetchall()}

def insert_player_alternate_positions(cur, df: pd.DataFrame, player_id_map: dict[str, int]):
    rows = []
    for _, row in df.iterrows():
        player_id = player_id_map.get(row['name'], None)
        if player_id is None:
            continue

        positions = row['positions'].split(",") if pd.notna(row['positions']) else []
        for i in range(1, len(positions)):
            rows.append((player_id, positions[i].strip()))

    execute_values(
        cur,
        """
            INSERT INTO player_alternate_positions (player_id, position) 
            VALUES %s
            ON CONFLICT DO NOTHING
        """,
        rows
    )

def insert_player_season_stats(cur, df: pd.DataFrame, player_id_map: dict[str, int]):
    rows = []
    for _, row in df.iterrows():
        player_id = player_id_map.get(row['name'], None)
        if player_id is None:
            continue

        vec = row['stats_vector']
        if vec is None or vec == 'None':
            continue
        if isinstance(vec, str):
            vec = ast.literal_eval(vec)
        
        vec_string ='[' + ','.join(f"{v:.8f}" for v in vec) + ']'

        minutes_played = row['minutes_played'] if pd.notna(row['minutes_played']) else 0

        rows.append((
            player_id, '2024/2025', minutes_played, _float(row, 'npxg_per_90'),  
            _float(row, 'shots_per_90'), _float(row, 'sot_per_90'), _float(row, 'headed_shots_per_90'),
            _float(row, 'xa_per_90'), _float(row, 'succ_pass_per_90'), _float(row, 'succ_pass_rate'),
            _float(row, 'acc_long_balls_per_90'), _float(row, 'succ_long_balls_rate'),
            _float(row, 'chances_created_per_90'), _float(row, 'big_chances_created_per_90'),
            _float(row, 'succ_crosses_per_90'), _float(row, 'succ_crosses_rate'), 
            _float(row, 'succ_dribbles_per_90'), _float(row, 'succ_dribbles_rate'),
            _float(row, 'duels_won_per_90'), _float(row, 'duels_won_rate'), 
            _float(row, 'aerials_won_per_90'), _float(row, 'aerials_won_rate'),
            _float(row, 'touches_per_90'), _float(row, 'touches_opp_box_per_90'),
            _float(row, 'dispossessed_per_90'), _float(row, 'fouls_won_per_90'), 
            _float(row, 'defcon_per_90'), _float(row, 'tackles_per_90'), 
            _float(row, 'interceptions_per_90'), _float(row, 'blocks_per_90'), 
            _float(row, 'fouls_committed_per_90'), _float(row, 'recoveries_per_90'), _float(row, 'poss_won_final_3rd_per_90'),
            _float(row, 'succ_dribbles_def_per_90'), _float(row, 'clearances_per_90'),
            vec_string
        ))

    execute_values(
        cur,
        """
            INSERT INTO player_season_stats (
                player_id, season, minutes_played, npxg_per90, shots_per90, shots_on_target_per90, 
                headed_shots_per90, xa_per90, successful_passes_per90, successful_pass_rate,
                accurate_long_balls_per90, accurate_long_balls_rate, chances_created_per90,
                big_chances_created_per90, successful_crosses_per90, successful_cross_rate,
                successful_dribbles_per90, successful_dribble_rate, duels_won_per90,
                duel_success_rate, aerial_duels_won_per90, aerial_duel_success_rate,
                touches_per90, opposition_box_touches_per90, dispossessed_per90,
                fouls_won_per90, defcon_per90, tackles_per90, interceptions_per90,
                blocks_per90, fouls_committed_per90, recoveries_per90,
                possession_won_final_third_per90, dribbled_past_per90,
                clearances_per90, stats_vector
            ) VALUES %s
            ON CONFLICT DO NOTHING
        """,
        rows
    )

def run():
    print("=" * 60)
    print("Phase 3 - Transform & Load")
    print("=" * 60)
 
    # --- Transform ---
    print("\n[1/2] Cleaning & vectorising...")
    df = load_and_clean_data()
    df = scale_features(df)
 
    # --- Load ---
    print("\n[2/2] Inserting into PostgreSQL...")
    conn = _connect_db()
    conn.autocommit = False
    cur = conn.cursor()
 
    try: 
        print("  -> countries")
        country_id_map = insert_countries(cur)
        print(f"     {len(country_id_map)} countries")

        print("\n  -> leagues")
        league_id_map = insert_leagues(cur, country_id_map)
        print(f"     {len(league_id_map)} leagues")

        print("  -> clubs")
        club_id_map = insert_clubs(cur, league_id_map)
        print(f"     {len(club_id_map)} clubs")
 
        print("  -> players")
        player_id_map = insert_players(cur, df, club_id_map, country_id_map)
        print(f"     {len(player_id_map)} players")
 
        print("  -> player_alternate_positions")
        insert_player_alternate_positions(cur, df, player_id_map)
 
        print("  -> player_season_stats")
        insert_player_season_stats(cur, df, player_id_map)
 
        conn.commit()
        print("\nOK: All data committed successfully.")
 
    except Exception as exc:
        conn.rollback()
        print(f"\nError - transaction rolled back.\n  {exc}")
        raise
 
    finally:
        cur.close()
        conn.close()
 
 
if __name__ == "__main__":
    run()
 