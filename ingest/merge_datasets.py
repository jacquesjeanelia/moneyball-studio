import pandas as pd
import os
from thefuzz import fuzz, process

def merge_sofascore_with_transfermarkt(player_stats_path="data/raw/player_stats.csv", transfermarkt_path="data/raw/transfermarkt_players.csv"):
    sofascore_path = player_stats_path
    transfermarkt_path = transfermarkt_path
    output_path = "data/raw/combined_player_dataset.csv"

    if not os.path.exists(sofascore_path) or not os.path.exists(transfermarkt_path):
        print("Error: Make sure both raw CSV files exist in data/raw/")
        return

    print("Loading datasets...")
    df_sofa = pd.read_csv(sofascore_path)
    df_tm = pd.read_csv(transfermarkt_path)

    tm_columns = [
        'name', 'date_of_birth', 'country_of_citizenship', 'position', 
        'foot', 'height_in_cm', 'image_url', 'market_value_in_eur'
    ]

    df_tm_filtered = df_tm[tm_columns].dropna(subset=['name']).copy()

    df_tm_filtered['market_value_in_eur'] = df_tm_filtered['market_value_in_eur'].fillna(0).astype(int)

    tm_names = df_tm_filtered['name'].tolist()

    print("Aligning player profiles using fuzzy string matching...")
    matched_rows = []

    total_players = len(df_sofa)
    count = 0

    for idx, sofa_row in df_sofa.iterrows():
        count += 1
        print(f"Processing player {idx + 1}/{total_players}: {sofa_row['player_name']}...", end='\r')
        sofa_name = sofa_row['player_name']
        
        best_match_name, score = process.extractOne(sofa_name, tm_names, scorer=fuzz.token_sort_ratio)
        
        if score >= 85:
            tm_row = df_tm_filtered[df_tm_filtered['name'] == best_match_name].iloc[0]
            
            combined_record = sofa_row.to_dict()
            combined_record['player_name'] = tm_row['name']
            combined_record['date_of_birth'] = tm_row['date_of_birth']
            combined_record['country_of_citizenship'] = tm_row['country_of_citizenship']
            combined_record['transfermarkt_position'] = tm_row['position'] # Named distinctly to avoid clash with sofa's position
            combined_record['preferred_foot'] = tm_row['foot']
            combined_record['height_in_cm'] = tm_row['height_in_cm']
            combined_record['player_photo_url'] = tm_row['image_url']
            combined_record['market_value_in_eur'] = tm_row['market_value_in_eur']
            
            matched_rows.append(combined_record)
            print(f"Matched '{sofa_name}' with '{best_match_name}' (Score: {score})")
        else:
            combined_record = sofa_row.to_dict()
            combined_record['player_name'] = None
            combined_record['date_of_birth'] = None
            combined_record['country_of_citizenship'] = None
            combined_record['transfermarkt_position'] = None
            combined_record['preferred_foot'] = None
            combined_record['height_in_cm'] = None
            combined_record['player_photo_url'] = None
            combined_record['market_value_in_eur'] = 0
            
            matched_rows.append(combined_record)
            print(f"No good match for '{sofa_name}' (Best: '{best_match_name}' with Score: {score})")

    final_df = pd.DataFrame(matched_rows)
    
    final_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\nSuccess! Combined dataset saved to: {output_path}")
    print(f"Total processed players: {len(final_df)}")

if __name__ == "__main__":
    merge_sofascore_with_transfermarkt()