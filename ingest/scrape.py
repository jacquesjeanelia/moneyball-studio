import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from pprint import pprint
import os
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
import kagglehub
from kagglehub import KaggleDatasetAdapter
from thefuzz import fuzz, process
from unidecode import unidecode

POSITION_MAP = {
    "Keeper": "GK",
    "Left Back": "LB",
    "Right Back": "RB",
    "Left Wing-Back": "LWB",
    "Right Wing-Back": "RWB",
    "Center Back": "CB",
    "Defensive Midfielder": "DM",
    "Central Midfielder": "CM",
    "Left Midfielder": "LM",
    "Right Midfielder": "RM",
    "Attacking Midfielder": "AM",
    "Left Winger": "LW",
    "Right Winger": "RW",
    "Striker": "ST",
}

os.environ["KAGGLE_USERNAME"] = "jacquessjeann"
os.environ["KAGGLE_KEY"] = "KGAT_9aa93aefd03c5492ac8231cf8e479cee"

with open(os.path.join('data', 'raw', 'fotmob_leagues.csv'), 'r') as f:
    reader = csv.reader(f)
    next(reader)
    LEAGUES = {int(rows[0]): (rows[1], rows[2]) for rows in reader} # league_id: (country_name, league_name)

def get_league_season_id(league_id: int = 47):
    """
        Get the season IDs for the 2025/2026, 2024/2025, and 2023/2024 seasons for a given Fotmob league
        Input:
            league_id: Fotmob league ID (int)
        Output:
            one: 2025/2026 season ID (int)
            two: 2024/2025 season ID (int)
            three: 2023/2024 season ID (int)
            is_two_year_season: True if the league has a two-year season format, False otherwise
    """

    url = f"https://www.fotmob.com/api/data/leagues?id={league_id}&ccode3=EGY"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    print(f"Connecting to user-facing endpoint: {url}")
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"HTTP Connection failed: {response.status_code}")
        return None
    one = two = three = None
    json = response.json()
    is_two_year_season = json['allAvailableSeasons'][0].split('/')[0] != json['allAvailableSeasons'][0]
    seasons = json['stats']['seasonStatLinks']
    if is_two_year_season:
        for season in seasons:
            if season['Name'] == "2025/2026":
                one = season['TournamentId']
            elif season['Name'] == "2024/2025":
                two = season['TournamentId']
            elif season['Name'] == "2023/2024":
                three = season['TournamentId']
                return one, two, three, is_two_year_season
    else:
        for season in seasons:
            if season['Name'] == "2026":
                one = season['TournamentId']
            if season['Name'] == "2025":
                two = season['TournamentId']
            if season['Name'] == "2024":
                three = season['TournamentId']
                return one, two, three, is_two_year_season
    return one, two, three, is_two_year_season

    
def get_all_league_season_ids():
    """
        Get the season IDs for all leagues in the LEAGUES dictionary
        Output:
            df_one: DataFrame containing season IDs for leagues with one-year seasons
            df_two: DataFrame containing season IDs for leagues with two-year seasons
    """

    one_year_seasons = []
    two_year_seasons = []
    for league_id, (league_name, country_name) in LEAGUES.items():
        one, two, three, is_two_year_season = get_league_season_id(league_id=league_id)
        if is_two_year_season:
            two_year_seasons.append((league_id, league_name, country_name, one, two, three))
        else:
            one_year_seasons.append((league_id, league_name, country_name, one, two, three))
    df_one = pd.DataFrame(one_year_seasons, columns=['league_id', 'league_name', 'country_name', '2025-2026_season_id', '2024-2025_season_id', '2023-2024_season_id'])
    df_two = pd.DataFrame(two_year_seasons, columns=['league_id', 'league_name', 'country_name', '2025-2026_season_id', '2024-2025_season_id', '2023-2024_season_id'])

    return df_one, df_two


def get_club(league_id: int = 47, season: str = "2025/2026"):
    """
    Get the clubs for a given Fotmob league and season
    Inputs:
        league_id: Fotmob league ID (int)
        season: Season format (str)
    Output:
        df: DataFrame containing 'league_id', 'team_id', and 'team_name'
    """

    f, s = season.split('/')
    url = f"https://www.fotmob.com/api/data/leagues?id={league_id}&ccode3=EGY&season={f}%2F{s}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    list = []

    print(f"Connecting to user-facing endpoint: {url}")
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"HTTP Connection failed: {response.status_code}")
        return None

    data = response.json()
    tables_list = []
    if data['table'] is None:
        response = requests.get(url, headers=headers)
        data = response.json()
        print("NONE")
    try:
        tables_list.append(data['table'][0]['data']['table']['all']) 
    except KeyError:
        tables = data['table'][0]['data']['tables']
        for i in range(len(tables)):
            tables_list.append(tables[i]['table']['all'])

    for table in tables_list:
        for team in table:
            team_id = team['id']
            team_name = team['name']
            list.append((league_id, team_id, team_name))

    df = pd.DataFrame(list, columns=['league_id', 'team_id', 'team_name'])
    return df


def get_all_clubs():
    """
    Get all clubs for all leagues in the LEAGUES dictionary
    """
    df = pd.DataFrame()
    for league_id, (league_name, country_name) in LEAGUES.items():
        new_df = get_club(league_id=league_id, season="2025/2026")
        if new_df is not None:
            df = pd.concat([df, new_df], ignore_index=True)
    df.to_csv(os.path.join('data', 'raw', f'fotmob_clubs.csv'), index=False)
    print(f"Data saved to data/raw/fotmob_clubs.csv")
    return df


def get_player_ids(league_id: int = 47, season_id: int = 27110, is_two_year_season: bool = True):
    """
        Get the player IDs for a given Fotmob league and season
        Inputs:
            league_id: Fotmob league ID (int)
            season_id: Fotmob season ID (int)
            is_two_year_season: True if the league has a two-year season format, False otherwise
        Output:
            df: DataFrame containing 'player_id', 'name', 'club_id', and 'season_type'
    """

    url = f"https://www.fotmob.com/api/data/leagueseasondeepstats?id={league_id}&season={season_id}&type=players&stat=mins_played"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print(f"Connecting to user-facing endpoint: {url}")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"HTTP Connection failed: {response.status_code}")
        return None
            
    data = response.json()
    stats_list = data['statsData']
    season_type = 2 if is_two_year_season else 1
    player_data = [(player['id'], player['name'], player['teamId'], season_type) for player in stats_list]

    df = pd.DataFrame(player_data, columns=['player_id', 'name', 'club_id', 'season_type'])
    return df

def get_all_players_ids():
    """
        Get all player IDs for all one and two-year leagues
        Output:
            df: DataFrame containing 'player_id', 'name', 'club_id', and 'season_type'
    """
    # df_one, df_two = get_all_league_season_ids()
    # dictionnary_one = {row['league_id']: row['2025-2026_season_id'] for _, row in df_one.iterrows()}
    # dictionnary_two = {row['league_id']: row['2025-2026_season_id'] for _, row in df_two.iterrows()}
    dictionnary_one = {}

    dictionnary_two = {
        47:  27110,
        48: 27195,
        108: 27196,
        109: 27197,
        117: 27309,
        9084: 1000000327,
    }
    
    df = pd.DataFrame()
    for league_id, season_id in dictionnary_one.items():
        league_name, country_name = LEAGUES[league_id]
        print(f"League: {league_name}, Country: {country_name}, league_id: {league_id}, Season ID: {season_id}")
        if season_id is None:
            continue
        new_df = get_player_ids(league_id=league_id, season_id=season_id, is_two_year_season=False)
        if new_df is not None:
            df = pd.concat([df, new_df], ignore_index=False)
        else:
            return None
    
    for league_id, season_id in dictionnary_two.items():
        league_name, country_name = LEAGUES[league_id]
        print(f"League: {league_name}, Country: {country_name}, league_id: {league_id}, Season ID: {season_id}")
        if season_id is None:
            continue
        new_df = get_player_ids(league_id=league_id, season_id=season_id, is_two_year_season=True)
        if new_df is not None:
            df = pd.concat([df, new_df], ignore_index=False)
        else:
            return None
    df.to_csv(os.path.join('data', 'raw', f'fotmob_players_ids.csv'), index=False)
    return df


def get_transfermarkt_league_ids():
    """
        Load league IDs from the Transfermarkt dataset on Kaggle.
        Loaded data format:
            'competition_id'
            'competition'
            'competition_url'
            'country_id'
            'country'
            'area_id'
            'area'
            'flag_url'
            'competition_list_url'
        Output:
            dataframe with columns 'competition_id' and 'competition'
    """
    print("Loading league_ids from Kaggle dataset...")
    df = kagglehub.dataset_load( 
        KaggleDatasetAdapter.PANDAS,
        "kberkek00/transfermarkt-datas",
        "TransferMarkt/competition_list.csv"
    )
    df = df[['competition_id', 'competition', 'country']]
    return df

def get_transfermarkt_club_ids():
    """
        Load club IDs from the Transfermarkt dataset on Kaggle.
        Loaded data format:
            'team_id'
            'team' 
            'team_url' 
            'competition_id' 
            'competition'
        Output:
            dataframe with columns 'team_id' and 'team'
    """
    print("Loading club_ids from Kaggle dataset...")
    df = kagglehub.dataset_load( 
        KaggleDatasetAdapter.PANDAS,
        "kberkek00/transfermarkt-datas",
        "TransferMarkt/team.csv"
    )
    df = df[['competition_id', 'team_id', 'team']]
    return df

def get_transfermarkt_player_ids():
    print("Loading player_ids from Kaggle dataset...")
    df = kagglehub.dataset_load(
        KaggleDatasetAdapter.PANDAS,
        "kberkek00/transfermarkt-datas",
        "TransferMarkt/player_list.csv"
    )
    df = df[['team_id', 'tmid', 'player']]
    return df

def merge_leagues():
    """
        Merge Transfermarkt league IDs with Fotmob league IDs using fuzzy string matching.
        Inputs: 
            Transfermarkt league IDs
            Fotmob league IDs
        Output:
            Dictionary mapping Transfermarkt competition_id to Fotmob league_id
    """
    df_tm_leagues = get_transfermarkt_league_ids()
    tm_leagues = df_tm_leagues['competition'].tolist()
    tm_leagues_cleaned = {unidecode(name): name for name in tm_leagues}
    tm_leagues_dict = {row['competition_id']: row['competition'] for _, row in df_tm_leagues.iterrows()}

    df_fotmob_leagues = pd.read_csv(os.path.join('data', 'raw', 'fotmob_leagues_test.csv'))
    df_mapping = pd.DataFrame(columns=['tm_competition_id', 'fotmob_league_id', 'score'])

    count = 0
    for idx, row in df_fotmob_leagues.iterrows():
        print(f"Processing league {count}/{len(df_fotmob_leagues)}: {row['league']}...", end='\r')
        count += 1

        fotmob_country = row['country']
        fotmob_league_name = row['league']
        fotmob_league_name_cleaned = unidecode(fotmob_league_name)

        tm_leagues = df_tm_leagues.loc[df_tm_leagues['country'] == fotmob_country, 'competition_id'].tolist()
        tm_dict = {row['competition_id']: row['competition'] for _, row in df_tm_leagues.iterrows() if row['competition_id'] in tm_leagues}
        # for ids in tm_leagues:
        #     print(f"Transfermarkt league ID: {ids}, League Name: {tm_leagues_dict[ids]}")
        tm_leagues_cleaned = {unidecode(tm_leagues_dict[ids]): tm_leagues_dict[ids] for ids in tm_leagues}
        # pprint(tm_leagues_cleaned)

        if not tm_leagues_cleaned:
            print(f"No Transfermarkt leagues found for country: {fotmob_country}")
            continue

        best_match_name, score = process.extractOne(fotmob_league_name_cleaned, list(tm_leagues_cleaned), scorer=fuzz.token_sort_ratio)
        # if score > 99:
        #     #print(f"Matched '{fotmob_league_name_cleaned}' with '{best_match_name}' (Score: {score})")
        original_name = tm_leagues_cleaned[best_match_name]
        for k, v in tm_dict.items():
            if v == original_name:
                competition_id = k
        # competition_id = tm_dict[tm_leagues_cleaned[best_match_name]]
        df_mapping = pd.concat([df_mapping, pd.DataFrame([{
            'tm_competition_id': competition_id,
            'tm_league_name': best_match_name,
            'fotmob_league_id': row['league_id'],
            'fotmob_league_name': fotmob_league_name,
            'score': score
        }])], ignore_index=True)
        # else:
        #     print(f"No good match for '{fotmob_league_name_cleaned}' (Best match: '{best_match_name}', Score: {score})")
    
    df_mapping.to_csv(os.path.join('data', 'raw', 'mapped_leagues.csv'), index=False)

def merge_clubs():
    """
        Merge Transfermarkt club IDs with Fotmob club IDs using fuzzy string matching.
        Inputs: 
            Transfermarkt club IDs
            Fotmob club IDs
        Output:
            Dictionary mapping Transfermarkt team_id to Fotmob Team ID
    """
    league_mapping_df = pd.read_csv(os.path.join('data', 'raw', 'mapped_leagues.csv'))
    league_map = {row['tm_competition_id']: row['fotmob_league_id'] for _, row in league_mapping_df.iterrows()}

    df_tm_clubs = get_transfermarkt_club_ids() # competition_id, team_id, team

    # df_fotmob_clubs = get_all_clubs()
    df_fotmob_clubs = pd.read_csv(os.path.join('data', 'raw', 'fotmob_clubs.csv'))
    tm_to_fotmob_mapping = {}

    for tm_id, fotmob_id in league_map.items():
        df_temp_tm = df_tm_clubs[df_tm_clubs['competition_id'] == tm_id]
        df_temp_fotmob = df_fotmob_clubs[df_fotmob_clubs['League ID'] == fotmob_id]
        tm_clubs = df_temp_tm['team'].tolist()
        tm_clubs_cleaned = {unidecode(name): name for name in tm_clubs}
        tm_clubs_dict = {row['team']: row['team_id'] for _, row in df_temp_tm.iterrows()}
        for idx, row in df_temp_fotmob.iterrows():
            fotmob_club_name = row['Team Name']
            fotmob_club_name_cleaned = unidecode(fotmob_club_name)
            best_match_name, score = process.extractOne(fotmob_club_name_cleaned, list(tm_clubs_cleaned), scorer=fuzz.token_sort_ratio)
            if score > 99:
                print(f"Matched '{fotmob_club_name_cleaned}' with '{best_match_name}' (Score: {score})")
                team_id = tm_clubs_dict[tm_clubs_cleaned[best_match_name]]
                tm_to_fotmob_mapping[team_id] = row['Team ID']
            else:
                # print(f"No good match for '{fotmob_club_name_cleaned}' (Best match: '{best_match_name}', Score: {score})")
                tm_updated_clubs = [f"{club.replace('FC ', '').replace('AFC', '')}" for club in tm_clubs_cleaned]
                best_match_name, score = process.extractOne(fotmob_club_name_cleaned, tm_updated_clubs, scorer=fuzz.token_sort_ratio)
                if score > 99:
                    print(f"Matched '{fotmob_club_name_cleaned}' with '{best_match_name}' (Score: {score})")
                    index = tm_updated_clubs.index(best_match_name)
                    original_name = tm_clubs[index]
                    team_id = tm_clubs_dict[original_name]
                    tm_to_fotmob_mapping[team_id] = row['Team ID']
                else:
                    # print(f"No good match for '{fotmob_club_name_cleaned}' (Best match: '{best_match_name}', Score: {score})")
                    tm_updated_clubs = [f"{club.split()[0]}" for club in tm_clubs_cleaned]
                    best_match_name, score = process.extractOne(fotmob_club_name_cleaned, tm_updated_clubs, scorer=fuzz.token_sort_ratio)
                    if score > 99:
                        print(f"Matched '{fotmob_club_name_cleaned}' with '{best_match_name}' (Score: {score})")
                        index = tm_updated_clubs.index(best_match_name)
                        original_name = tm_clubs[index]
                        team_id = tm_clubs_dict[original_name]
                        tm_to_fotmob_mapping[team_id] = row['Team ID']
                    else:
                        fotmob_updated_club_name = fotmob_club_name_cleaned.split()[0]
                        best_match_name, score = process.extractOne(fotmob_updated_club_name, tm_updated_clubs, scorer=fuzz.token_sort_ratio)
                        if score > 99:
                            print(f"Matched '{fotmob_club_name_cleaned}' with '{best_match_name}' (Score: {score})")
                            index = tm_updated_clubs.index(best_match_name)
                            original_name = tm_clubs[index]
                            team_id = tm_clubs_dict[original_name]
                            tm_to_fotmob_mapping[team_id] = row['Team ID']
                        else:
                            fotmob_updated_club_name = fotmob_club_name_cleaned.split()[-1]
                            best_match_name, score = process.extractOne(fotmob_updated_club_name, tm_updated_clubs, scorer=fuzz.token_sort_ratio)
                            if score > 99:
                                print(f"Matched '{fotmob_club_name_cleaned}' with '{best_match_name}' (Score: {score})")
                                index = tm_updated_clubs.index(best_match_name)
                                original_name = tm_clubs[index]
                                team_id = tm_clubs_dict[original_name]
                                tm_to_fotmob_mapping[team_id] = row['Team ID']
                            else:
                                # print(f"No good match for '{fotmob_club_name_cleaned}' (Best match: '{best_match_name}', Score: {score})")
                                tm_updated_clubs = [f"{club.split()[-1]}" for club in tm_clubs_cleaned]
                                best_match_name, score = process.extractOne(fotmob_club_name_cleaned, tm_updated_clubs, scorer=fuzz.token_sort_ratio)
                                if score > 99:
                                    print(f"Matched '{fotmob_club_name_cleaned}' with '{best_match_name}' (Score: {score})")
                                    index = tm_updated_clubs.index(best_match_name)
                                    original_name = tm_clubs[index]
                                    team_id = tm_clubs_dict[original_name]
                                    tm_to_fotmob_mapping[team_id] = row['Team ID']
                                else:
                                    fotmob_updated_club_name = fotmob_club_name_cleaned.split()[0]
                                    best_match_name, score = process.extractOne(fotmob_updated_club_name, tm_updated_clubs, scorer=fuzz.token_sort_ratio)
                                    if score > 99:
                                        print(f"Matched '{fotmob_club_name_cleaned}' with '{best_match_name}' (Score: {score})")
                                        index = tm_updated_clubs.index(best_match_name)
                                        original_name = tm_clubs[index]
                                        team_id = tm_clubs_dict[original_name]
                                        tm_to_fotmob_mapping[team_id] = row['Team ID']
                                    else:
                                        # print(f"No good match for '{fotmob_club_name_cleaned}' (Best match: '{best_match_name}', Score: {score})")
                                        fotmob_updated_club_name = fotmob_club_name_cleaned.split()[-1]
                                        best_match_name, score = process.extractOne(fotmob_updated_club_name, tm_updated_clubs, scorer=fuzz.token_sort_ratio)
                                        if score > 99:
                                            print(f"Matched '{fotmob_club_name_cleaned}' with '{best_match_name}' (Score: {score})")
                                            index = tm_updated_clubs.index(best_match_name)
                                            original_name = tm_clubs[index]
                                            team_id = tm_clubs_dict[original_name]
                                            tm_to_fotmob_mapping[team_id] = row['Team ID']
                                        else:
                                            print(f"No good match for '{fotmob_club_name_cleaned}' (Best match: '{best_match_name}', Score: {score})")
    final_df = pd.DataFrame(list(tm_to_fotmob_mapping.items()), columns=['tm_team_id', 'fotmob_team_id'])
    final_df.to_csv(os.path.join('data', 'raw', 'mapped_clubs.csv'), index=False)
    return tm_to_fotmob_mapping

def merge_players():
    """
        Merge Transfermarkt player IDs with Fotmob player IDs using fuzzy string matching.
        Inputs:
            Transfermarkt player IDs
            Fotmob player IDs
        Output:
            Dictionary mapping Transfermarkt tmid to Fotmob player_id
    """
    club_mapping_df = pd.read_csv(os.path.join('data', 'raw', 'mapped_clubs.csv'))
    # pprint(club_mapping_df)
    club_map = {row['tm_team_id']: row['fotmob_team_id'] for _, row in club_mapping_df.iterrows()}

    df_tm_players = get_transfermarkt_player_ids() # team_id, tmid, player

    df_fotmob_players = pd.read_csv(os.path.join('data', 'raw', 'fotmob_players_ids.csv')) # player_id, name, club_id, season_type
    tm_to_fotmob_mapping = pd.DataFrame(columns=['tm_player_id', 'fotmob_player_id', 'player'])

    for tm_id, fotmob_id in club_map.items(): # iterate over clubs
        print('='*50)
        print(tm_id, fotmob_id)
        df_temp_tm = df_tm_players[df_tm_players['team_id'] == tm_id]
        df_temp_fotmob = df_fotmob_players[df_fotmob_players['club_id'] == fotmob_id]
        tm_players = df_temp_tm['player'].tolist()
        tm_players_cleaned = {unidecode(name): name for name in tm_players}
        tm_players_dict = {row['player']: row['tmid'] for _, row in df_temp_tm.iterrows()}
        # pprint(list(tm_players_cleaned.keys()))
        # print(df_temp_fotmob)
        tm_players_list = list(tm_players_cleaned.keys())
        for idx, row in df_temp_fotmob.iterrows(): # iterate over fotmob players in the club
                fotmob_name = row['name']
                fotmob_name_cleaned = unidecode(fotmob_name)
                # print(fotmob_name_cleaned)
                
                best_match_name, score = process.extractOne(fotmob_name_cleaned, tm_players_list, scorer=fuzz.token_sort_ratio)
                if score > 95:
                    # tm_row = df_tm_players[df_tm_players['player'] == tm_players_cleaned[best_match_name]].iloc[0]
                    # fotmob_df.at[idx, 'transfermarkt_player_id'] = tm_row['tmid']
                    # print(f"Matched '{fotmob_name_cleaned}' with '{best_match_name}' (Score: {score})")
                    tm_player_id = tm_players_dict[tm_players_cleaned[best_match_name]]
                    tm_to_fotmob_mapping.loc[len(tm_to_fotmob_mapping)] = [tm_player_id, row['player_id'], row['name']]
                else:
                    # print(f"No good match for '{fotmob_name_cleaned}' (Best match: '{best_match_name}', Score: {score}) - trying alternative matching strategies...")
                    parts = fotmob_name_cleaned.split()
                    parts = fotmob_name_cleaned.split()
                    if len(parts) > 2:
                        fotmob_name_cleaned = f"{parts[0]} {parts[1]}"
                        best_match_name, score = process.extractOne(fotmob_name_cleaned, tm_players_list, scorer=fuzz.token_sort_ratio)
                        # print(f"Trying first + middle: '{fotmob_name_cleaned}' and '{best_match_name}' (Score: {score})")
                        if score > 95:
                            # tm_row = df_tm_players[df_tm_players['player'] == tm_players_cleaned[best_match_name]].iloc[0]
                            # fotmob_df.at[idx, 'transfermarkt_player_id'] = tm_row['tmid']
                            # print(f"Matched '{fotmob_name_cleaned}' with '{best_match_name}' (Score: {score})")
                            tm_player_id = tm_players_dict[tm_players_cleaned[best_match_name]]
                            tm_to_fotmob_mapping.loc[len(tm_to_fotmob_mapping)] = [tm_player_id, row['player_id'], row['name']]
                        else:
                            fotmob_name_cleaned = f"{parts[1]} {parts[2]}"
                            best_match_name, score = process.extractOne(fotmob_name_cleaned, tm_players_list, scorer=fuzz.token_sort_ratio)
                            # print(f"Trying middle + last: '{fotmob_name_cleaned}' and '{best_match_name}' (Score: {score})")    
                            if score > 95:
                                # tm_row = df_tm_players[df_tm_players['player'] == tm_players_cleaned[best_match_name]].iloc[0]
                                # fotmob_df.at[idx, 'transfermarkt_player_id'] = tm_row['tmid']
                                # print(f"Matched '{fotmob_name_cleaned}' with '{best_match_name}' (Score: {score})")
                                tm_player_id = tm_players_dict[tm_players_cleaned[best_match_name]]
                                tm_to_fotmob_mapping.loc[len(tm_to_fotmob_mapping)] = [tm_player_id, row['player_id'], row['name']]
                            else:
                                fotmob_name_cleaned = f"{parts[0]} {parts[2]}"
                                best_match_name, score = process.extractOne(fotmob_name_cleaned, tm_players_list, scorer=fuzz.token_sort_ratio)
                                # print(f"Trying first + last: '{fotmob_name_cleaned}' and '{best_match_name}' (Score: {score})")     
                                if score > 95:
                                    # tm_row = df_tm_players[df_tm_players['player'] == tm_players_cleaned[best_match_name]].iloc[0]
                                    # fotmob_df.at[idx, 'transfermarkt_player_id'] = tm_row['tmid']
                                    # print(f"Matched '{fotmob_name_cleaned}' with '{best_match_name}' (Score: {score})")
                                    tm_player_id = tm_players_dict[tm_players_cleaned[best_match_name]]
                                    tm_to_fotmob_mapping.loc[len(tm_to_fotmob_mapping)] = [tm_player_id, row['player_id'], row['name']]
                    elif len(parts) > 1:
                        fotmob_name_cleaned = parts[0]
                        best_match_name, score = process.extractOne(fotmob_name_cleaned, tm_players_list, scorer=fuzz.token_sort_ratio)
                        # print(f"Trying first name only: '{fotmob_name_cleaned}' and '{best_match_name}' (Score: {score})")
                        if score > 95:
                            # tm_row = df_tm_players[df_tm_players['player'] == tm_players_cleaned[best_match_name]].iloc[0]
                            # fotmob_df.at[idx, 'transfermarkt_player_id'] = tm_row['tmid']
                            # print(f"Matched '{fotmob_name_cleaned}' with '{best_match_name}' (Score: {score})")
                            tm_player_id = tm_players_dict[tm_players_cleaned[best_match_name]]
                            tm_to_fotmob_mapping.loc[len(tm_to_fotmob_mapping)] = [tm_player_id, row['player_id'], row['name']]
                        else:
                            if len(parts) > 1:
                                fotmob_name_cleaned = parts[-1]
                            best_match_name, score = process.extractOne(fotmob_name_cleaned, tm_players_list, scorer=fuzz.token_sort_ratio)
                            # print(f"Trying last name only: '{fotmob_name_cleaned}' and '{best_match_name}' (Score: {score})")
                            if score > 95:
                                # tm_row = df_tm_players[df_tm_players['player'] == tm_players_cleaned[best_match_name]].iloc[0]
                                # fotmob_df.at[idx, 'transfermarkt_player_id'] = tm_row['tmid']
                                # print(f"Matched '{fotmob_name_cleaned}' with '{best_match_name}' (Score: {score})")
                                tm_player_id = tm_players_dict[tm_players_cleaned[best_match_name]]
                                tm_to_fotmob_mapping.loc[len(tm_to_fotmob_mapping)] = [tm_player_id, row['player_id'], row['name']]


                            else:
                                fotmob_name_cleaned = ' '.join(parts)
                                # print(f"No good match for '{fotmob_name_cleaned}' (Best match: '{best_match_name}', Score: {score})")

                                # print(f"No good match for '{fotmob_name_cleaned}' (Best match: '{best_match_name}', Score: {score}) - try keeping first name in TM")
                                temp_players_list = [name.split()[0] for name in tm_players_list]
                                # temp_df = df_temp_tm['player'].str.replace(r'^(\S+)\s+.*\s+(\S+)$', r'\1 \2', regex=True)
                                # tm = temp_df.tolist()
                                # tm_players_cleaned = {unidecode(name): name for name in tm}
                                best_match_name, score = process.extractOne(fotmob_name_cleaned, temp_players_list, scorer=fuzz.token_sort_ratio)
                                if score > 95:
                                    # tm_row = df_tm_players[df_tm_players['player'] == tm_players_cleaned[best_match_name]].iloc[0]
                                    # fotmob_df.at[idx, 'transfermarkt_player_id'] = tm_row['tmid']
                                    # print(f"Matched '{fotmob_name_cleaned}' with '{best_match_name}' (Score: {score})")
                                    tm_player_id = tm_players_dict[tm_players_cleaned[best_match_name]]
                                    tm_to_fotmob_mapping.loc[len(tm_to_fotmob_mapping)] = [tm_player_id, row['player_id'], row['name']]
                                else:
                                    temp_players_list = [name.split()[-1] for name in tm_players_list]
                                    # temp_df['player'] = df_temp_tm['player'].str.replace(r'^(\S+)\s+(\S+).*$', r'\1 \2', regex=True)
                                    # tm = temp_df['player'].tolist()
                                    # tm_players_cleaned = {unidecode(name): name for name in tm}
                                    best_match_name, score = process.extractOne(fotmob_name_cleaned, temp_players_list, scorer=fuzz.token_sort_ratio)
                                    # print(f"No good match for '{fotmob_name_cleaned}' (Best match: '{best_match_name}', Score: {score}) - try keeping last name in TM")
                                    if score > 95:
                                        # tm_row = df_tm_players[df_tm_players['player'] == tm_players_cleaned[best_match_name]].iloc[0]
                                        # fotmob_df.at[idx, 'transfermarkt_player_id'] = tm_row['tmid']
                                        # print(f"Matched '{fotmob_name_cleaned}' with '{best_match_name}' (Score: {score})")
                                        tm_player_id = tm_players_dict[tm_players_cleaned[best_match_name]]
                                        tm_to_fotmob_mapping.loc[len(tm_to_fotmob_mapping)] = [tm_player_id, row['player_id'], row['name']]
                                    elif len(parts) > 2:
                                            # print(f"No good match for '{fotmob_name_cleaned}' (Best match: '{best_match_name}', Score: {score}) - try keeping first name in TM")
                                            temp_players_list = [name.split()[0:1] for name in tm_players_list]
                                            # temp_df['player'] = df_temp_tm['player'].str.replace(r'^\S+\s+(\S+)(?:\s+.*\s+|\s+)(\S+)$', r'\1 \2', regex=True)
                                            # tm = temp_df['player'].tolist()
                                            # tm_players_cleaned = {unidecode(name): name for name in tm}
                                            best_match_name, score = process.extractOne(fotmob_name_cleaned, temp_players_list, scorer=fuzz.token_sort_ratio)
                                            # print(f"No good match for '{fotmob_name_cleaned}' (Best match: '{best_match_name}', Score: {score}) - try removing first name in TM")    
                                            if score > 95:
                                                # tm_row = df_tm_players[df_tm_players['player'] == tm_players_cleaned[best_match_name]].iloc[0]
                                                # fotmob_df.at[idx, 'transfermarkt_player_id'] = tm_row['tmid']
                                                # print(f"Matched '{fotmob_name_cleaned}' with '{best_match_name}' (Score: {score})")
                                                tm_player_id = tm_players_dict[tm_players_cleaned[best_match_name]]
                                                tm_to_fotmob_mapping.loc[len(tm_to_fotmob_mapping)] = [tm_player_id, row['player_id'], row['name']]
                                            else:
                                                print(f"No good match for '{fotmob_name_cleaned}' (Best match: '{best_match_name}', Score: {score})")
                                                # fotmob_df.at[idx, 'transfermarkt_player_id'] = None
                                    else:
                                        print(f"No good match for '{fotmob_name_cleaned}' (Best match: '{best_match_name}', Score: {score})")
                                        # fotmob_df.at[idx, 'transfermarkt_player_id'] = None
    tm_to_fotmob_mapping.to_csv(os.path.join('data', 'raw', 'mapped_players.csv'), index=False)
    return tm_to_fotmob_mapping


def get_player_price(tm_id: int = 937958):
    url = f"https://tmapi.transfermarkt.technology/players?ids[]={tm_id}"
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.9",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print(f"Connecting to user-facing endpoint: {url}")
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching player price for ID {tm_id}")
        return None
    json = response.json()
    try:
        value = json['data'][0]['marketValueDetails']['current']['value']
    except (KeyError, IndexError):
        print(f"Error extracting player price for ID {tm_id}")
        return None
    return value

def _get_single_player_price(player_data):
    player_id, tm_id = player_data
    print(f"Fetching price for FotMob ID: {player_id}, Transfermarkt ID: {tm_id}")
    try:
        price = get_player_price(tm_id)
        print(price)
        if price is None:
            print(f"Failed: {player_id} (ID: {tm_id}) - No data returned.")
        return player_id, price
    except Exception as e:
        print(f"Error: {player_id} (ID: {tm_id}) - {e}")
        return None
    
def get_all_players_prices():
    fotmob_df = merge_clubs()
    players_list = [(row['player_id'], row['transfermarkt_player_id']) for _, row in fotmob_df.iterrows() if pd.notnull(row['transfermarkt_player_id'])]
    out_file_path = os.path.join('data', 'raw', 'transfermarkt_players_values.csv')

    processed_ids = set()
    if os.path.exists(out_file_path):
        try:
            existing_df = pd.read_csv(out_file_path, usecols=['player_id'])
            processed_ids = set(existing_df['player_id'].dropna().astype(int))
            print(f"Found {len(processed_ids)} already processed players. Skipping them...")
        except Exception as e:
            print(f"Could not read existing CSV for resume check: {e}")

    players_to_fetch = [p for p in players_list if p[0] not in processed_ids]

    if not players_to_fetch:
        print("All players have already been processed!")
        return pd.read_csv(out_file_path)
    
    max_workers = 10
    print(f"Starting parallel fetch for {len(players_to_fetch)} players with {max_workers} threads...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_player = {executor.submit(_get_single_player_price, p): p for p in players_to_fetch}

        for future in as_completed(future_to_player):
            result = future.result()
            if result is not None:
                player_id, price = result
                write_header = not os.path.exists(out_file_path)
                pd.DataFrame([[player_id, price]], columns=['player_id', 'transfermarkt_value']).to_csv(
                    out_file_path,
                    mode='a',
                    header=write_header,
                    index=False
                )
                print(f"Saved: FotMob ID: {player_id}, Price: {price}")

    print("\nScraping complete!")
    return pd.read_csv(out_file_path)


def get_player_info(fotmob_id: int = 292462, tm_id: int = 937958):
    """
    Get detailed player information for a given Fotmob player ID
    Input:
        fotmob_id: Fotmob player ID (int)
        tm_id: Transfermarkt player ID (int)
    Output:
        tuple: (fotmob_id, name, date_of_birth, height_in_cm, preferred_foot, country_of_citizenship, primary_position, positions)
    """
    price = get_player_price(tm_id)
    url = f"https://www.fotmob.com/api/data/playerData?id={fotmob_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    print(f"Connecting to user-facing endpoint: {url}")

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"HTTP Connection failed: {response.status_code}")
        return None

    json = response.json()
    name = json['name']
    dob = json['birthDate']['utcTime']

    height_cm = None
    foot = None
    country = None

    player_info = json['playerInformation']
    for info in player_info:
        if info['title'] == "Height":
            height_cm = info['value']['numberValue']
        elif info['title'] == "Preferred foot":
            foot = info['value']['key']
        elif info['title'] == "Country":
            country = info['value']['fallback']
    
    primary_position = POSITION_MAP[json['positionDescription']['primaryPosition']['label']] if json['positionDescription']['primaryPosition']['label'] in POSITION_MAP.keys() else json['positionDescription']['primaryPosition']['label']
    try:
        position_info = json['positionDescription']['nonPrimaryPositions']
    except KeyError:
        position_info = []
    positions = []
    for p in position_info:
        positions.append(POSITION_MAP[p['label']] if p['label'] in POSITION_MAP.keys() else p['label'])
    positions = ','.join(positions) if positions else None
    return (fotmob_id, tm_id, name, dob, height_cm, foot, country, primary_position, positions, price)


def _process_single_player_info(player_data):
    fotmob_id, tm_id, name = player_data
    try:
        player_info = get_player_info(fotmob_id=fotmob_id, tm_id=tm_id)
        if player_info is None:
            print(f"Failed: (Fotmob ID: {fotmob_id}, Transfermarkt ID: {tm_id}) - No data returned.")
        return player_info
    except Exception as e:
        print(f"Error: (Fotmob ID: {fotmob_id}, Transfermarkt ID: {tm_id}) - {e}")
        return None
    
def get_all_players_info():
    df_mapped = pd.read_csv(os.path.join('data', 'raw', 'mapped_players.csv'))
    players_list = [(row['fotmob_player_id'], row['tm_player_id'], row['player']) for _, row in df_mapped.iterrows()]

    processed_ids = set()
    if os.path.exists(os.path.join('data', 'raw', 'fotmob_players_info.csv')):
        try:
            existing_df = pd.read_csv(os.path.join('data', 'raw', 'fotmob_players_info.csv'), usecols=['player_id'])
            processed_ids = set(existing_df['player_id'].dropna())
            print(f"Found {len(processed_ids)} already processed players. Skipping them...")
        except Exception as e:
            print(f"Error reading existing file: {e}")

    players_to_fetch = [p for p in players_list if p[0] not in processed_ids]

    if not players_to_fetch:
        print("All players have already been processed.")
        return pd.read_csv(os.path.join('data', 'raw', 'fotmob_players_info.csv'))
    
    max_workers = 10
    print(f"Starting parallel processing with {max_workers} workers...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_player = {executor.submit(_process_single_player_info, player): player for player in players_to_fetch}

        for future in as_completed(future_to_player):
            stats = future.result()

            if stats is not None:
                write_header = not os.path.exists(os.path.join('data', 'raw', 'fotmob_players_info.csv'))
                pd.DataFrame([stats], columns=['fotmob_id', 'tm_id', 'name', 'dob', 'height_cm', 'preferred_foot', 'country', 'category', 'positions', 'value']).to_csv(
                    os.path.join('data', 'raw', 'fotmob_players_info.csv'), 
                    mode='a', 
                    header=write_header, 
                    index=False
                )
                print(f"Successfully processed: {stats[1]} (ID: {stats[0]})")
    print("All players processed. Data saved to data/raw/fotmob_players_info.csv")
    return pd.read_csv(os.path.join('data', 'raw', 'fotmob_players_info.csv'))


def get_player_stats(player_id: int = 292462, club_id: int = 8650, is_two_year_season: bool = True):
    player = {
        "player_id": player_id,
        "club_id": club_id,
        "minutes_played": None,
        "npxg_per_90": None,
        "shots_per_90": None,
        "sot_per_90": None,
        "headed_shots_per_90": None,
        "xa_per_90": None,
        "succ_pass_per_90": None,
        "succ_pass_rate": None,
        "acc_long_balls_per_90": None,
        "succ_long_balls_rate": None,
        "chances_created_per_90": None,
        "big_chances_created_per_90": None,
        "succ_crosses_per_90": None,
        "succ_crosses_rate": None,
        "succ_dribbles_per_90": None,
        "succ_dribbles_rate": None,
        "duels_won_per_90": None,
        "duels_won_rate": None,
        "aerials_won_per_90": None,
        "aerials_won_rate": None,
        "touches_per_90": None,
        "touches_opp_box_per_90": None,
        "dispossessed_per_90": None,
        "fouls_won_per_90": None,
        "defcon_per_90": None,
        "tackles_per_90": None,
        "interceptions_per_90": None,
        "blocks_per_90": None,
        "fouls_committed_per_90": None,
        "recoveries_per_90": None,
        "poss_won_final_3rd_per_90": None,
        "succ_dribbles_def_per_90": None,
        "clearances_per_90": None
    }

    url = f"https://www.fotmob.com/api/data/playerData?id={player_id}"
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "cookie": "_gcl_au=1.1.543096671.1780835303; _ga=GA1.1.991595523.1780835303; _pubcid=47534508-996a-42a3-89ad-76345befc5f7; NEXT_LOCALE=en;", # Truncated for readability; keep yours full
        "priority": "u=1, i",
        "referer": "https://www.fotmob.com/teams/568727/overview/gimnasia-mendoza",
        "sec-ch-ua": '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        "x-mas": "eyJib2R5Ijp7InVybCI6Ii9hcGkvZGF0YS90bHRhYmxlP2xlYWd1ZUlkPTExMiZ0ZWFtcz0lNUI1Njg3MjclNUQiLCJjb2RlIjoxNzgyMTU3MjI4MDQ2LCJmb28iOiJwcm9kdWN0aW9uOjRlYjM1Y2Q3MjIyMWNkMzVhYjI4NzJkOGQ0NTQ2YjUzY2I0NjU0YzcifSwic2lnbmF0dXJlIjoiNDlEQjcwNTIwNUMxMDNERENCMjQwRDhFNEE4NzBDQTgifQ=="
    }
    print(f"Connecting to user-facing endpoint: {url}")

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f" {player_id}: HTTP Connection failed: {response.status_code}")
        return None
    
    json = response.json()
    try:
        position = json['positionDescription']['positions'][0]['strPosShort']['label']
    except (KeyError, IndexError):
        position = json['positionDescription']['primaryPosition']['label']
    pprint(f"Player {player_id} position: {position}")
    if position == 'GK' or position == 'keeper':
        return None  # Skip goalkeepers as they have different stats
    
    recent_matches = json['recentMatches']
    scraped_team_id = recent_matches[0]['teamId'] if recent_matches else None
    try:
        all_stats = json['firstSeasonStats']['statsSection']['items']
        player['minutes_played'] = None
        tabs = json['firstSeasonStats']['topStatCard']['items']
        # pprint(tabs)
        for t in tabs:
            if t['localizedTitleId'] == 'minutes_played':
                player["minutes_played"] = t['statValue']
    except (KeyError, TypeError):
        url = f"https://www.fotmob.com/api/data/playerStats?playerId={player_id}&seasonId=1-0&isFirstSeason=false"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f" {player_id}: HTTP Connection failed: {response.status_code}")
            return None
        print(f" {player_id}: Connecting to user-facing endpoint: {url}")
        json = response.json()
        player["minutes_played"] = json['topStatCard']['items'][5]['statValue'] 
        all_stats = json['statsSection']['items']
        # print(f" {player_id}: Error: 'firstSeasonStats' or 'statsSection' not found in JSON response")
        # return None


    print({player_id, scraped_team_id, club_id})
    if is_two_year_season and scraped_team_id != club_id:
        url = f"https://www.fotmob.com/api/data/playerStats?playerId={player_id}&seasonId=1-0&isFirstSeason=false"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f" {player_id}: HTTP Connection failed: {response.status_code}")
            return None
        print(f" {player_id}: Connecting to user-facing endpoint: {url}")
        json = response.json()
        player["minutes_played"] = json['topStatCard']['items'][5]['statValue'] 
        all_stats = json['statsSection']['items']
    if all_stats is None or len(all_stats) < 1:
        print(f" {player_id}: No stats found for player")
        return None

    shooting_stats = all_stats[0] 

    for stat in shooting_stats['items']:
        if stat['localizedTitleId'] == "non_penalty_xg":
            player["npxg_per_90"] = stat['per90']
        elif stat['localizedTitleId'] == "shots":
            player["shots_per_90"] = stat['per90']
        elif stat['localizedTitleId'] == "ShotsOnTarget":
            player["sot_per_90"] = stat['per90']
        elif stat['localizedTitleId'] == "headed_shots":
            player["headed_shots_per_90"] = stat['per90']

    passing_stats = all_stats[1]
    i = 1

    if len(passing_stats['items']) > i and passing_stats['items'][i]['localizedTitleId'] == "expected_assists":
        player["xa_per_90"] = passing_stats['items'][i]['per90']
        i += 1

    if len(passing_stats['items']) > i and passing_stats['items'][i]['localizedTitleId'] == "successful_passes":
        player["succ_pass_per_90"] = passing_stats['items'][i]['per90']
        i += 1

    if len(passing_stats['items']) > i and passing_stats['items'][i]['localizedTitleId'] == "successful_passes_accuracy":
        player["succ_pass_rate"] = passing_stats['items'][i]['per90']
        i += 1

    if len(passing_stats['items']) > i and passing_stats['items'][i]['localizedTitleId'] == "long_balls_accurate":
        player["acc_long_balls_per_90"] = passing_stats['items'][i]['per90']
        i += 1

    if len(passing_stats['items']) > i and passing_stats['items'][i]['localizedTitleId'] == "long_ball_succeeeded_accuracy":
        player["succ_long_balls_rate"] = passing_stats['items'][i]['per90']
        i += 1

    if len(passing_stats['items']) > i and passing_stats['items'][i]['localizedTitleId'] == "chances_created":
        player["chances_created_per_90"] = passing_stats['items'][i]['per90']
        i += 1

    if len(passing_stats['items']) > i and passing_stats['items'][i]['localizedTitleId'] == "big_chance_created_team_title":
        player["big_chances_created_per_90"] = passing_stats['items'][i]['per90']
        i += 1

    if len(passing_stats['items']) > i and passing_stats['items'][i]['localizedTitleId'] == "crosses_succeeeded":
        player["succ_crosses_per_90"] = passing_stats['items'][i]['per90']
        i += 1

    if len(passing_stats['items']) > i and passing_stats['items'][i]['localizedTitleId'] == "crosses_succeeeded_accuracy":
        player["succ_crosses_rate"] = passing_stats['items'][i]['per90']
    
    
    possession_stats = all_stats[2]
    i = 0

    if len(possession_stats['items']) > i and possession_stats['items'][i]['localizedTitleId'] == "dribbles_succeeded":
        player["succ_dribbles_per_90"] = possession_stats['items'][i]['per90']
        i += 1

    if len(possession_stats['items']) > i and possession_stats['items'][i]['localizedTitleId'] == "won_contest_subtitle":
        player["succ_dribbles_rate"] = possession_stats['items'][i]['per90'] 
        i += 1

    if len(possession_stats['items']) > i and possession_stats['items'][i]['localizedTitleId'] == "duel_won":
        player["duels_won_per_90"] = possession_stats['items'][i]['per90']
        i += 1

    if len(possession_stats['items']) > i and possession_stats['items'][i]['localizedTitleId'] == "duel_won_percent":
        player["duels_won_rate"] = possession_stats['items'][i]['per90']
        i += 1

    if len(possession_stats['items']) > i and possession_stats['items'][i]['localizedTitleId'] == "aerials_won":
        player["aerials_won_per_90"] = possession_stats['items'][i]['per90']
        i += 1

    if len(possession_stats['items']) > i and possession_stats['items'][i]['localizedTitleId'] == "aerials_won_percent":
        player["aerials_won_rate"] = possession_stats['items'][i]['per90']
        i += 1

    if len(possession_stats['items']) > i and possession_stats['items'][i]['localizedTitleId'] == "touches":
        player["touches_per_90"] = possession_stats['items'][i]['per90']
        i += 1

    if len(possession_stats['items']) > i and possession_stats['items'][i]['localizedTitleId'] == "touches_opp_box":
        player["touches_opp_box_per_90"] = possession_stats['items'][i]['per90']
        i += 1

    if len(possession_stats['items']) > i and possession_stats['items'][i]['localizedTitleId'] == "dispossessed":
        player["dispossessed_per_90"] = possession_stats['items'][i]['per90']
        i += 1

    if len(possession_stats['items']) > i and possession_stats['items'][i]['localizedTitleId'] == "fouls_won":
        player["fouls_won_per_90"] = possession_stats['items'][i]['per90']
    

    defending_stats = all_stats[3]
    i = 0

    if len(defending_stats['items']) > i and defending_stats['items'][i]['localizedTitleId'] == "defensive_actions":
        player["defcon_per_90"] = defending_stats['items'][i]['per90'] 
        i += 1

    if len(defending_stats['items']) > i and defending_stats['items'][i]['localizedTitleId'] == "matchstats.headers.tackles":
        player["tackles_per_90"] = defending_stats['items'][i]['per90']
        i += 1

    if len(defending_stats['items']) > i and defending_stats['items'][i]['localizedTitleId'] == "interceptions":
        player["interceptions_per_90"] = defending_stats['items'][i]['per90']
        i += 1

    if len(defending_stats['items']) > i and defending_stats['items'][i]['localizedTitleId'] == "blocked_shots":
        player["blocks_per_90"] = defending_stats['items'][i]['per90']
        i += 1

    if len(defending_stats['items']) > i and defending_stats['items'][i]['localizedTitleId'] == "fouls":
        player["fouls_committed_per_90"] = defending_stats['items'][i]['per90']
        i += 1
    
    if len(defending_stats['items']) > i and defending_stats['items'][i]['localizedTitleId'] == "recoveries":
        player["recoveries_per_90"] = defending_stats['items'][i]['per90']
        i += 1
    
    if len(defending_stats['items']) > i and defending_stats['items'][i]['localizedTitleId'] == "poss_won_att_3rd_team_title":
        player["poss_won_final_3rd_per_90"] = defending_stats['items'][i]['per90']
        i += 1
    
    if len(defending_stats['items']) > i and defending_stats['items'][i]['localizedTitleId'] == "dribbled_past":
        player["succ_dribbles_def_per_90"] = defending_stats['items'][i]['per90']
        i += 1
    
    if len(defending_stats['items']) > i and defending_stats['items'][i]['localizedTitleId'] == "clearances":
        player["clearances_per_90"] = defending_stats['items'][i]['per90']
        i += 1
    
    return player


def _process_single_player_stats(player_data):
    """Helper function to process a single player for the thread pool."""
    player_id, club_id, season_type = player_data
    is_two_year_season = True if season_type == 2 else False
    
    try:
        player_stats = get_player_stats(
            player_id=int(player_id), 
            club_id=int(club_id), 
            is_two_year_season=is_two_year_season
        )
        
        if player_stats is None:
            print(f"Failed: (ID: {player_id}) - No data returned.")
            
        return player_stats
    except Exception as e:
        print(f"Error: (ID: {player_id}) - {e}")
        return None

def get_all_players_stats():
    # 1. Read input data
    with open(os.path.join('data', 'raw', 'fotmob_players_ids.csv'), 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader) # Skip header
        players_list = [(int(rows[0]), int(rows[2]), int(rows[3])) for rows in reader]

    out_file_path = os.path.join('data', 'raw', 'fotmob_players_stats.csv')
    
    # 2. Check existing data to enable resuming
    processed_ids = set()
    if os.path.exists(out_file_path):
        try:
            # Read existing IDs to skip them
            existing_df = pd.read_csv(out_file_path, usecols=['player_id'])
            processed_ids = set(existing_df['player_id'].dropna().astype(int))
            print(f"Found {len(processed_ids)} already processed players. Skipping them...")
        except Exception as e:
            print(f"Could not read existing CSV for resume check: {e}")

    # Filter out players we already have
    players_to_fetch = [p for p in players_list if p[0] not in processed_ids]
    
    if not players_to_fetch:
        print("All players have already been processed!")
        return pd.read_csv(out_file_path)

    # 3. Parallelize the API calls
    max_workers = 10 
    print(f"Starting parallel fetch for {len(players_to_fetch)} players with {max_workers} threads...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_player = {executor.submit(_process_single_player_stats, p): p for p in players_to_fetch}
        
        # 4. Save immediately as each thread completes (in the main thread)
        for future in as_completed(future_to_player):
            stats = future.result()
            
            if stats is not None:
                # If the file doesn't exist yet, write the header. Otherwise, append without header.
                write_header = not os.path.exists(out_file_path)
                
                # Append the single row directly to the CSV
                pd.DataFrame([stats], columns=stats.keys()).to_csv(
                    out_file_path, 
                    mode='a', 
                    header=write_header, 
                    index=False
                )
                print(f"Saved: {stats.get('player_name')} (ID: {stats.get('player_id')})")

    print("\nScraping complete!")
    return pd.read_csv(out_file_path)



def run():
    print("Getting all players IDs...")
    get_all_players_ids()
    print("Getting all players information...")
    get_all_players_info()
    print("Getting all players statistics...")
    get_all_players_stats()

if __name__ == "__main__":
    # run()
    # get_all_players_ids()
    # merge_clubs()
    get_all_players_info()
    # get_all_players_stats()
    # print(get_player_stats(player_id=966026, club_id=10252, is_two_year_season=True))