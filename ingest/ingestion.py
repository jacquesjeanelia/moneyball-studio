import pandas as pd
from ScraperFC import Sofascore
import os

def get_player_stats_dataset(year="24/25", league="England Premier League"):
    scraper = Sofascore()
    
    print(f"Scraping total seasonal metrics for {league}...")
    df = scraper.scrape_player_league_stats(
        year=year, 
        league=league, 
        accumulation="total"
    )

    cols_to_numeric = [
        'expectedGoals', 'expectedAssists', 'shotsOnTarget', 
        'accurateFinalThirdPasses', 'successfulDribbles', 'accuratePassesPercentage',
        'tackles', 'interceptions', 'aerialDuelsWonPercentage', 
        'ballRecovery', 'fouls', 'penaltiesTaken', 'minutesPlayed'
    ]
    
    for col in cols_to_numeric:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    df = df[df['minutesPlayed'] >= 450].copy()
    print(f"-> Filtered down to {len(df)} players with >= 450 total minutes.")


    df['scaling_factor'] = df['minutesPlayed'] / 90.0
    
    # Avoid dividing by zero if any remaining player has 0 minutes
    df['scaling_factor'] = df['scaling_factor'].replace(0, 1.0)

    df['npxG_total'] = df['expectedGoals'] - (df['penaltiesTaken'] * 0.78) # Assuming an average penalty conversion rate of 78%
    df['npxG_total'] = df['npxG_total'].clip(lower=0)
    
    df['npxg_per90'] = df['npxG_total'] / df['scaling_factor']
    df['xa_per90'] = df['expectedAssists'] / df['scaling_factor']
    df['shots_on_target_per90'] = df['shotsOnTarget'] / df['scaling_factor']
    df['progressive_passes_per90'] = df['accurateFinalThirdPasses'] / df['scaling_factor']
    df['successful_dribbles_per90'] = df['successfulDribbles'] / df['scaling_factor']
    df['tackles_interceptions_per90'] = (df['tackles'] + df['interceptions']) / df['scaling_factor']
    df['ball_recoveries_per90'] = df['ballRecovery'] / df['scaling_factor']
    df['fouls_committed_per90'] = df['fouls'] / df['scaling_factor']
    
    df['pass_completion_percentage'] = df['accuratePassesPercentage']
    df['aerial_duels_won_percentage'] = df['aerialDuelsWonPercentage']

    feature_mapping = {
        'player': 'player_name',
        'team': 'club',
        'minutesPlayed': 'minutes_played',
        'npxg_per90': 'npxg_per90',
        'xa_per90': 'xa_per90',
        'shots_on_target_per90': 'shots_on_target_per90',
        'progressive_passes_per90': 'progressive_passes_per90', 
        'successful_dribbles_per90': 'successful_dribbles_per90',
        'pass_completion_percentage': 'pass_completion_percentage',
        'tackles_interceptions_per90': 'tackles_interceptions_per90',
        'aerial_duels_won_percentage': 'aerial_duels_won_percentage',
        'ball_recoveries_per90': 'ball_recoveries_per90',
        'fouls_committed_per90': 'fouls_committed_per90'
    }
    
    available_keys = [k for k in feature_mapping.keys() if k in df.columns]
    final_df = df[available_keys].rename(columns=feature_mapping)
    final_df = final_df.dropna(subset=['player_name'])
    return final_df

def get_club_dataset(league="England Premier League", year="24/25"):
    scraper = Sofascore()
    club_records = []

    print(f"\nExtracting structural image URLs for: {league}...")
    try:
        df = scraper.scrape_team_league_stats(year=year, league=league)
        cols = df.columns.tolist()
        
        team_id_col = next((c for c in cols if 'team' in c.lower() and 'id' in c.lower()), None)
        team_name_col = next((c for c in cols if 'team' in c.lower() and 'name' in c.lower() or c.lower() == 'team'), None)
        
        if team_name_col:
            sub_df = df[[team_name_col] + ([team_id_col] if team_id_col else [])].drop_duplicates()
            for _, row in sub_df.iterrows():
                club_name = row[team_name_col]
                t_id = row[team_id_col] if team_id_col and pd.notna(row[team_id_col]) else None
                
                club_records.append({
                    "League": league,
                    "Club Name": club_name,
                    "Club Image URL": f"https://api.sofascore.app/api/v1/team/{int(t_id)}/image" if t_id else "Unknown"
                })
                
    except Exception as e:
        print(f"Error extracting data for {league}: {e}")

    os.makedirs("data/raw", exist_ok=True)
    return club_records

def get_all_leagues(leagues=["England Premier League"], years=["24/25"]):
    all_players_df = pd.DataFrame()
    all_clubs = []
    for league in leagues:
        for year in years:
            try:
                league_df = get_player_stats_dataset(year=year, league=league)
                all_players_df = pd.concat([all_players_df, league_df], ignore_index=True)
                all_clubs.extend(get_club_dataset(league=league, year=year))
            except Exception as e:
                print(f"Error processing {league} for year {year}: {e}")

    print(f"\nData processing complete. Final dataset contains {len(all_players_df)} rows.")
    
    os.makedirs("data/raw", exist_ok=True)
    pd.DataFrame(all_clubs).to_csv("data/raw/club_data.csv", index=False, encoding='utf-8')
    print("Saved club data to data/raw/club_data.csv")
    all_players_df.to_csv("data/raw/player_stats.csv", index=False, encoding='utf-8')
    print("Saved clean raw data to data/raw/player_stats.csv")

def get_transfermarkt_dataset():
    transfermarkt_url = "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data/players.csv.gz"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("Streaming data from Transfermarkt R2 bucket...")
    sheet = pd.read_csv(
        transfermarkt_url, 
        compression='gzip', 
        storage_options=headers
    )

    sheet.to_csv("data/raw/transfermarkt_players.csv", index=False, encoding='utf-8-sig')
    print("Saved transfermarkt player data to data/raw/transfermarkt_players.csv")    

if __name__ == "__main__":
    get_all_leagues(["England Premier League", "Spain La Liga", "Italy Serie A", "France Ligue 1", "Germany Bundesliga"], ["24/25"])
    # get_transfermarkt_dataset()
