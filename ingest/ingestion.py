import pandas as pd
from ScraperFC import Sofascore
import os
from thefuzz import fuzz, process
import soccerdata as sd
import requests


def merge_datasets(player_stats_path="data/raw/player_stats.csv", transfermarkt_path="data/raw/transfermarkt_players.csv", eafc_path="data/raw/player_images.csv"):
    sofascore_path = player_stats_path
    transfermarkt_path = transfermarkt_path
    eafc_path = eafc_path
    output_path = "data/raw/combined_player_dataset.csv"

    if not os.path.exists(sofascore_path) or not os.path.exists(transfermarkt_path):
        print("Error: Make sure both raw CSV files exist in data/raw/")
        return

    print("Loading datasets...")
    df_sofa = pd.read_csv(sofascore_path)
    df_tm = pd.read_csv(transfermarkt_path)
    df_eafc = pd.read_csv(eafc_path)

    tm_columns = [
        'name', 'date_of_birth', 'country_of_citizenship', 'position', 
        'foot', 'height_in_cm', 'image_url', 'market_value_in_eur'
    ]
    df_tm_filtered = df_tm[tm_columns].dropna(subset=['name']).copy()
    df_tm_filtered['market_value_in_eur'] = df_tm_filtered['market_value_in_eur'].fillna(0).astype(int)
    tm_names = df_tm_filtered['name'].tolist()

    eafc_columns = ['name', 'positions', 'face_url']
    df_eafc_filtered = df_eafc[eafc_columns].dropna(subset=['name']).copy()
    eafc_names = df_eafc_filtered['name'].tolist()

    print("Aligning player profiles using fuzzy string matching...")
    matched_rows = []

    total_players = len(df_sofa)
    count = 0

    for idx, sofa_row in df_sofa.iterrows():
        count += 1
        print(f"Processing player {idx + 1}/{total_players}: {sofa_row['player_name']}...", end='\r')
        sofa_name = sofa_row['player_name']
        
        tm_best_match_name, score1 = process.extractOne(sofa_name, tm_names, scorer=fuzz.token_sort_ratio)
        eafc_best_match_name, score2 = process.extractOne(tm_best_match_name, eafc_names, scorer=fuzz.token_sort_ratio)

        
        if score1 >= 85 and score2 >= 85:
            tm_row = df_tm_filtered[df_tm_filtered['name'] == tm_best_match_name].iloc[0]
            eafc_row = df_eafc_filtered[df_eafc_filtered['name'] == eafc_best_match_name].iloc[0]

            combined_record = sofa_row.to_dict()
            combined_record['player_name'] = eafc_row['name']
            combined_record['date_of_birth'] = tm_row['date_of_birth']
            combined_record['country_of_citizenship'] = tm_row['country_of_citizenship']
            combined_record['transfermarkt_position'] = tm_row['position'] # Named distinctly to avoid clash with sofa's position
            combined_record['positions'] = eafc_row['positions']
            combined_record['preferred_foot'] = tm_row['foot']
            combined_record['height_in_cm'] = tm_row['height_in_cm']
            combined_record['player_photo_url'] = eafc_row['face_url']
            combined_record['market_value_in_eur'] = tm_row['market_value_in_eur']

            matched_rows.append(combined_record)
            print(f"Matched '{sofa_name}' with '{tm_best_match_name}' with '{eafc_best_match_name}' (Scores: {score1}, {score2})")
        else:
            combined_record = sofa_row.to_dict()
            combined_record['player_name'] = None
            combined_record['date_of_birth'] = None
            combined_record['country_of_citizenship'] = None
            combined_record['transfermarkt_position'] = None
            combined_record['positions'] = None
            combined_record['preferred_foot'] = None
            combined_record['height_in_cm'] = None
            combined_record['player_photo_url'] = None
            combined_record['market_value_in_eur'] = 0
            matched_rows.append(combined_record)
            print(f"No good match for '{sofa_name}' (Best: '{tm_best_match_name}' with Score: {score1}, '{eafc_best_match_name}' with Score: {score2})")

    final_df = pd.DataFrame(matched_rows)
    
    final_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\nSuccess! Combined dataset saved to: {output_path}")
    print(f"Total processed players: {len(final_df)}")


if __name__ == "__main__":
    merge_datasets()
