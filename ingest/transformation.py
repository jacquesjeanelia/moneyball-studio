from operator import pos
import os
import ast
import pprint
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import psycopg2
from psycopg2.extras import execute_values
from umap import UMAP
import csv

PLAYER_ROLES = {
    "ST": "Striker",
    "LW": "Winger", "RW": "Winger",
    "LM": "Wide Midfielder", "RM": "Wide Midfielder",
    "AM": "Creative Attacker",
    "CM": "Midfielder", "DM": "Midfielder",
    "LWB": "Fullback", "RWB": "Fullback", 
    "LB": "Fullback", "RB": "Fullback",
    "CB": "Center Back",
    "GK": "Goalkeeper"
}

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

PLAYER_INFO_PATH = "data/raw/fotmob_players_full_info.csv"
PLAYER_STATS_PATH = "data/raw/fotmob_players_stats.csv"
COUNTRIES_PATH = "data/raw/total/countries_data.csv"
LEAGUES_PATH = "data/raw/total/fotmob_leagues.csv"
CLUBS_PATH = "data/raw/total/fotmob_clubs.csv"
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
    df_info = df_info.rename(columns={'fotmob_id': 'player_id'})
    df_stats = safe_read_csv(PLAYER_STATS_PATH)

    # Merge dataframes on player_id
    df_merged = pd.merge(df_info, df_stats, on='player_id', how='inner')
    return df_merged

def load_and_clean_data():
    df = merge_player_data()
    df = df[df['minutes_played'] >= 450]
    df = df[df['name'].notnull()]
    df[FEATURE_COLS] = df[FEATURE_COLS].fillna(0)
    df['dob'] = df['dob'].str.slice(0, 10)
    df = df[df['category'].str.lower() != 'keeper']
    df = df[~df['positions'].str.contains('GK', na=False)]
    # df.to_csv("data/processed/cleaned_player_dataset.csv", index=False, encoding='utf-8')
    return df

def get_percentiles():
    df = load_and_clean_data()
    df['main_role'] = df['category'].map(PLAYER_ROLES)
    df['npxg_percentile'] = df.groupby('main_role')['npxg_per_90'].rank(pct=True) * 100
    df['shots_percentile'] = df.groupby('main_role')['shots_per_90'].rank(pct=True) * 100
    df['sot_percentile'] = df.groupby('main_role')['sot_per_90'].rank(pct=True) * 100
    df['headed_shots_percentile'] = df.groupby('main_role')['headed_shots_per_90'].rank(pct=True) * 100
    df['xa_percentile'] = df.groupby('main_role')['xa_per_90'].rank(pct=True) * 100
    df['succ_pass_percentile'] = df.groupby('main_role')['succ_pass_per_90'].rank(pct=True) * 100
    df['succ_pass_rate_percentile'] = df.groupby('main_role')['succ_pass_rate'].rank(pct=True) * 100
    df['acc_long_balls_percentile'] = df.groupby('main_role')['acc_long_balls_per_90'].rank(pct=True) * 100
    df['succ_long_balls_rate_percentile'] = df.groupby('main_role')['succ_long_balls_rate'].rank(pct=True) * 100
    df['chances_created_percentile'] = df.groupby('main_role')['chances_created_per_90'].rank(pct=True) * 100
    df['big_chances_created_percentile'] = df.groupby('main_role')['big_chances_created_per_90'].rank(pct=True) * 100
    df['succ_crosses_percentile'] = df.groupby('main_role')['succ_crosses_per_90'].rank(pct=True) * 100
    df['succ_crosses_rate_percentile'] = df.groupby('main_role')['succ_crosses_rate'].rank(pct=True) * 100
    df['succ_dribbles_percentile'] = df.groupby('main_role')['succ_dribbles_per_90'].rank(pct=True) * 100
    df['succ_dribbles_rate_percentile'] = df.groupby('main_role')['succ_dribbles_rate'].rank(pct=True) * 100
    df['duels_won_percentile'] = df.groupby('main_role')['duels_won_per_90'].rank(pct=True) * 100
    df['duels_won_rate_percentile'] = df.groupby('main_role')['duels_won_rate'].rank(pct=True) * 100
    df['aerials_won_percentile'] = df.groupby('main_role')['aerials_won_per_90'].rank(pct=True) * 100
    df['aerials_won_rate_percentile'] = df.groupby('main_role')['aerials_won_rate'].rank(pct=True) * 100
    df['touches_percentile'] = df.groupby('main_role')['touches_per_90'].rank(pct=True) * 100
    df['touches_opp_box_percentile'] = df.groupby('main_role')['touches_opp_box_per_90'].rank(pct=True) * 100
    df['dispossessed_percentile'] = df.groupby('main_role')['dispossessed_per_90'].rank(pct=True, ascending=False) * 100
    df['fouls_won_percentile'] = df.groupby('main_role')['fouls_won_per_90'].rank(pct=True) * 100
    df['defcon_percentile'] = df.groupby('main_role')['defcon_per_90'].rank(pct=True) * 100
    df['tackles_percentile'] = df.groupby('main_role')['tackles_per_90'].rank(pct=True) * 100
    df['interceptions_percentile'] = df.groupby('main_role')['interceptions_per_90'].rank(pct=True) * 100
    df['blocks_percentile'] = df.groupby('main_role')['blocks_per_90'].rank(pct=True) * 100
    df['fouls_committed_percentile'] = df.groupby('main_role')['fouls_committed_per_90'].rank(pct=True, ascending=False) * 100
    df['recoveries_percentile'] = df.groupby('main_role')['recoveries_per_90'].rank(pct=True) * 100
    df['poss_won_final_3rd_percentile'] = df.groupby('main_role')['poss_won_final_3rd_per_90'].rank(pct=True) * 100
    df['succ_dribbles_def_percentile'] = df.groupby('main_role')['succ_dribbles_def_per_90'].rank(pct=True) * 100
    df['clearances_percentile'] = df.groupby('main_role')['clearances_per_90'].rank(pct=True) * 100

    # df.to_csv("data/processed/cleaned_player_dataset_with_roles.csv", index=False, encoding='utf-8')
    return df

def scale_features():
    df = get_percentiles()

    # Scale using Z-score normalization (mean=0, std=1)
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(df[FEATURE_COLS])

    # # ======================================================================================================================================
    # # TODO: Clustering to generate role tags
    # z_cols = [f"{col}_z" for col in FEATURE_COLS]
    # scaled_df = pd.DataFrame(scaled_features, columns=z_cols, index=df.index)
    # df = pd.concat([df, scaled_df], axis=1)

    # striker_df = df[df['main_role'] == 'Striker'].copy()

    # striker_highlight_cols = [
    #     'shots_per_90_z', 
    #     'touches_opp_box_per_90_z', 
    #     'succ_dribbles_per_90_z',  
    #     'chances_created_per_90_z',
    #     'headed_shots_per90_z',
    #     'xa_per90_z',
    # ]

    # X = striker_df[striker_highlight_cols]

    # kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    # striker_df['cluster_id'] = kmeans.fit_predict(X)

    # centroids = pd.DataFrame(kmeans.cluster_centers_, columns=striker_highlight_cols)
    # centroids.to_csv("data/processed/striker_centroids.csv", index=False, encoding='utf-8')

    # # creative_df = df[df['main_role'] == 'Creative Attacker'].copy()
    # # X = creative_df[['sot_per_90_z', 'xa_per_90_z', 'succ_crosses_per_90_z', 'succ_dribbles_per_90_z', 'tackles_per_90_z']]

    # return
    # # ======================================================================================================================================

    # PCA for dimensionality reduction to 17 dimensions (to remove overlap and redundancy in features)
    pca = PCA(n_components=17)
    pca_stats = pca.fit_transform(scaled_features)

    df['stats_vector'] = [str(list(vector.tolist())) for vector in pca_stats]

    # Separate volume and rate columns
    rate_cols = [c for c in FEATURE_COLS if 'rate' in c]
    volume_cols = [c for c in FEATURE_COLS if 'rate' not in c]

    # 1. Volume stats: 0 really means 0
    df[volume_cols] = df[volume_cols].fillna(0)

    # 2. Rate stats: If NaN (0/0 attempts), fill with positional average/median
    for col in rate_cols:
        df[col] = df.groupby('main_role')[col].transform(lambda x: x.fillna(x.median()))

    # UMAP for further dimensionality reduction to 2D for visualization and similarity search
    reducer = UMAP(n_neighbors=15, min_dist=0.1, n_components=2, random_state=42)
    umap_embedding = reducer.fit_transform(pca_stats)

    df['umap_x'] = umap_embedding[:, 0]
    df['umap_y'] = umap_embedding[:, 1]

    # 1. Split the dataset by the UMAP x-axis gap (adjust threshold if needed)
    left_island = df[df['umap_x'] < -1]
    left_island.to_csv("data/processed/left_island_players.csv", index=False, encoding='utf-8')

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


def insert_players(cur, df: pd.DataFrame, club_id_map: dict[str, int], country_id_map: dict[str, int]) -> dict[int, int]:
    rows = []
    fotmob_player_ids = []
    df = df.drop_duplicates(subset=['player_id'], keep='first').copy()
    df['dob'] = df['dob'].astype(str).str.strip()
    df['dob'] = pd.to_datetime(df['dob'], dayfirst=True, format='mixed', errors='coerce').dt.date
    for _, row in df.iterrows():
        fotmob_player_id = int(row['player_id']) if pd.notna(row['player_id']) else None
        if fotmob_player_id is None:
            continue

        country_id = country_id_map.get(row['country'], None)
        club_id = club_id_map.get(row['team_id'], None)
        name = row['name'] if pd.notna(row['name']) else None
        dob = row['dob'] if pd.notna(row['dob']) else None
        value = int(row['transfermarkt_value']) if pd.notna(row['transfermarkt_value']) else 0
        height = int(row['height_cm']) if pd.notna(row['height_cm']) else None
        main_position = row['category']
        foot = row['preferred_foot'] if pd.notna(row['preferred_foot']) else None
        photo_url = PLAYER_IMAGE_URL + f"{fotmob_player_id}.png"

        rows.append((
            name,
            dob,
            main_position,
            foot,
            height,
            club_id,
            country_id,
            photo_url,
            value
        ))
        fotmob_player_ids.append(fotmob_player_id)

    inserted_rows = execute_values(
        cur,
        """
            INSERT INTO players (
                name, date_of_birth, main_position, preferred_foot, height_cm, club_id, country_id, photo_url, current_market_value_eur
            ) VALUES %s
            RETURNING id
        """,
        rows,
        fetch=True
    )
    return {fotmob_player_id: db_id for fotmob_player_id, (db_id,) in zip(fotmob_player_ids, inserted_rows)}

def insert_player_alternate_positions(cur, df: pd.DataFrame, player_id_map: dict[int, int]):
    rows = []
    for _, row in df.iterrows():
        fotmob_player_id = int(row['player_id']) if pd.notna(row['player_id']) else None
        player_id = player_id_map.get(fotmob_player_id, None)
        if player_id is None:
            continue

        positions = row['positions'].split(",") if pd.notna(row['positions']) else []
        if not positions:
            continue
        for position in positions:
            rows.append((player_id, position.strip()))

    execute_values(
        cur,
        """
            INSERT INTO player_alternate_positions (player_id, position) 
            VALUES %s
            ON CONFLICT DO NOTHING
        """,
        rows
    )

def insert_player_season_stats(cur, df: pd.DataFrame, player_id_map: dict[int, int], club_id_map: dict[int, int]):
    rows = []
    for _, row in df.iterrows():
        fotmob_player_id = int(row['player_id']) if pd.notna(row['player_id']) else None
        player_id = player_id_map.get(fotmob_player_id, None)
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
            
            _float(row, 'npxg_percentile'),  
            _float(row, 'shots_percentile'), _float(row, 'sot_percentile'), _float(row, 'headed_shots_percentile'),
            _float(row, 'xa_percentile'), _float(row, 'succ_pass_percentile'), _float(row, 'succ_pass_rate_percentile'),
            _float(row, 'acc_long_balls_percentile'), _float(row, 'succ_long_balls_rate_percentile'),
            _float(row, 'chances_created_percentile'), _float(row, 'big_chances_created_percentile'),
            _float(row, 'succ_crosses_percentile'), _float(row, 'succ_crosses_rate_percentile'), 
            _float(row, 'succ_dribbles_percentile'), _float(row, 'succ_dribbles_rate_percentile'),
            _float(row, 'duels_won_percentile'), _float(row, 'duels_won_rate_percentile'), 
            _float(row, 'aerials_won_percentile'), _float(row, 'aerials_won_rate_percentile'),
            _float(row, 'touches_percentile'), _float(row, 'touches_opp_box_percentile'),
            _float(row, 'dispossessed_percentile'), _float(row, 'fouls_won_percentile'), 
            _float(row, 'defcon_percentile'), _float(row, 'tackles_percentile'), 
            _float(row, 'interceptions_percentile'), _float(row, 'blocks_percentile'), 
            _float(row, 'fouls_committed_percentile'), _float(row, 'recoveries_percentile'), _float(row, 'poss_won_final_3rd_percentile'),
            _float(row, 'succ_dribbles_def_percentile'), _float(row, 'clearances_percentile'),   

            row['umap_x'], row['umap_y'],
            vec_string
        ))

    execute_values(
        cur,
        """
            INSERT INTO player_season_stats (
                player_id, season, minutes_played, 
                
                npxg_per90, shots_per90, shots_on_target_per90, 
                headed_shots_per90, xa_per90, successful_passes_per90, successful_pass_rate,
                accurate_long_balls_per90, accurate_long_balls_rate, chances_created_per90,
                big_chances_created_per90, successful_crosses_per90, successful_cross_rate,
                successful_dribbles_per90, successful_dribble_rate, duels_won_per90,
                duel_success_rate, aerial_duels_won_per90, aerial_duel_success_rate,
                touches_per90, opposition_box_touches_per90, dispossessed_per90,
                fouls_won_per90, defcon_per90, tackles_per90, interceptions_per90,
                blocks_per90, fouls_committed_per90, recoveries_per90,
                possession_won_final_third_per90, dribbled_past_per90,
                clearances_per90, 

                npxg_percentile, shots_percentile, shots_on_target_percentile, 
                headed_shots_percentile, xa_percentile, successful_passes_percentile, successful_pass_rate_percentile,
                accurate_long_balls_percentile, accurate_long_balls_rate_percentile, chances_created_percentile,
                big_chances_created_percentile, successful_crosses_percentile, successful_cross_rate_percentile,
                successful_dribbles_percentile, successful_dribble_rate_percentile, duels_won_percentile,
                duel_success_rate_percentile, aerial_duels_won_percentile, aerial_duel_success_rate_percentile,
                touches_percentile, opposition_box_touches_percentile, dispossessed_percentile,
                fouls_won_percentile, defcon_percentile, tackles_percentile, interceptions_percentile,
                blocks_percentile, fouls_committed_percentile, recoveries_percentile,
                possession_won_final_third_percentile, dribbled_past_percentile,
                clearances_percentile,

                umap_x, umap_y,
                stats_vector
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
    df = scale_features()
 
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
        insert_player_season_stats(cur, df, player_id_map, club_id_map)
 
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
 