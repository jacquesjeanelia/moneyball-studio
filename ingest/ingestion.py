import pandas as pd
from ScraperFC import Sofascore
import os

def get_sofascore_dataset(year="24/25", league="England Premier League"):
    scraper = Sofascore()
    
    df = scraper.scrape_player_league_stats(
        year=year, 
        league=league, 
        accumulation="per90"
    )

    cols_to_numeric = [
        'expectedGoals', 'expectedAssists', 'shotsOnTarget', 
        'accurateFinalThirdPasses', 'successfulDribbles', 'accuratePassesPercentage',
        'tackles', 'interceptions', 'aerialDuelsWonPercentage', 
        'outfielderBlocks', 'ballRecovery', 'fouls', 'penaltiesTaken'
    ]
    
    for col in cols_to_numeric:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    df['npxG_per90'] = df['expectedGoals'] - (df['penaltiesTaken'] * 0.78)
    df['npxG_per90'] = df['npxG_per90'].clip(lower=0) 
    
    df['tackles_interceptions_per90'] = df['tackles'] + df['interceptions']
    feature_mapping = {
        'player': 'player_name',
        'team': 'club',
        'npxG_per90': 'npxG_per_90',
        'expectedAssists': 'xAG_per_90',
        'shotsOnTarget': 'shots_on_target_per_90',
        'accurateFinalThirdPasses': 'prog_passes_proxy_per_90', 
        'successfulDribbles': 'successful_takeons_per_90',
        'accuratePassesPercentage': 'pass_completion_pct',
        'tackles_interceptions_per90': 'tackles_interceptions_per_90',
        'aerialDuelsWonPercentage': 'aerial_duels_pct',
        'outfielderBlocks': 'blocks_per_90',
        'ballRecovery': 'ball_recoveries_per_90',
        'fouls': 'fouls_committed_per_90'
    }
    
    final_df = df[list(feature_mapping.keys())].rename(columns=feature_mapping)
    final_df = final_df.dropna(subset=['player_name'])
    return final_df

def get_all_leagues(leagues=["England Premier League"], year="24/25"):
    all_leagues_df = pd.DataFrame()
    for league in leagues:
        print(f"Processing league: {league}")
        league_df = get_sofascore_dataset(year=year, league=league)
        all_leagues_df = pd.concat([all_leagues_df, league_df], ignore_index=True)

    print(f"Data processing complete. Final dataset contains {len(all_leagues_df)} player rows with {len(all_leagues_df.columns)} features.")
    return all_leagues_df


if __name__ == "__main__":
    leagues = [
        "England Premier League", 
        "Spain La Liga", 
        "Italy Serie A", 
    ]
    player_metrics_df = get_all_leagues(leagues=leagues, year="24/25")
    os.makedirs("data/raw", exist_ok=True)
    player_metrics_df.to_csv("data/raw/player_stats_24_25.csv", index=False)
