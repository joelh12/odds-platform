# scrapers/pinnacle_esports.py

import requests
from pydantic import BaseModel
from datetime import datetime, timezone
import json
import os

# Provide these via environment variables instead of hardcoding secrets.
X_API_KEY = os.getenv("PINNACLE_API_KEY", "")
DEVICE_UUID = os.getenv("PINNACLE_DEVICE_UUID", "")

HEADERS = {
    "User-Agent": "EsportsOddsBot/1.0",
    "x-api-key": X_API_KEY,
    "x-device-uuid": DEVICE_UUID,
    "accept": "application/json",
    "content-type": "application/json"
}

class MatchOdds(BaseModel):
    teams: str
    odds: list[int]
    scraped_at: datetime

def scrape_pinnacle_esports() -> list[MatchOdds]:
    # Fetch all esports matchups for the Esports league (ID 12)
    list_url = "https://guest.api.arcadia.pinnacle.se/0.1/leagues/12/matchups?brandId=0"
    resp = requests.get(list_url, headers=HEADERS, timeout=10)
    # Handle No Content
    if resp.status_code == 204:
        related = []
    else:
        resp.raise_for_status()
        try:
            related = resp.json()
        except ValueError:
            # Dump response for debugging
            error_msg = (
                f"Failed to decode JSON from {list_url}\n"
                f"Status code: {resp.status_code}\n"
                f"Response body:\n{resp.text[:500]!r}"
            )
            raise RuntimeError(error_msg)

    # Build matchupId -> (home_name, away_name)
    mapping = {}
    for item in related:
        mid = item.get("id") or item.get("matchupId")
        participants = item.get("participants", [])
        home = next((p.get("name") for p in participants if p.get("alignment") == "home"), None)
        away = next((p.get("name") for p in participants if p.get("alignment") == "away"), None)
        if home is None and len(participants) > 0:
            home = participants[0].get("name")
        if away is None and len(participants) > 1:
            away = participants[1].get("name")
        if home and away:
            mapping[mid] = (home, away)

    # 2. Fetch straight odds for each matchup and merge
    straight_tpl = "https://guest.api.arcadia.pinnacle.se/0.1/matchups/{}/markets/related/straight"
    results = []

    for mid, (home, away) in mapping.items():
        url2 = straight_tpl.format(mid)
        r2 = requests.get(url2, headers=HEADERS, timeout=10)
        r2.raise_for_status()
        odds_data = r2.json()
        # find period 0 moneyline
        for entry in odds_data:
            if entry.get("type") == "moneyline" and entry.get("period") == 0:
                prices = entry.get("prices", [])
                home_price = next((p["price"] for p in prices if p.get("designation") == "home"), None)
                away_price = next((p["price"] for p in prices if p.get("designation") == "away"), None)
                results.append(MatchOdds(
                    teams=f"{home} vs {away}",
                    odds=[home_price, away_price],
                    scraped_at=datetime.now(timezone.utc)
                ))
                break

    return results

def format_price(price):
    """Convert American odds to decimal odds"""
    if price > 0:
        return round((price / 100) + 1, 2)
    else:
        return round((100 / abs(price)) + 1, 2)

def get_period_name(period):
    """Convert period number to meaningful description"""
    period_names = {
        '0': 'Match',
        '1': 'Map 1',
        '2': 'Map 2',
        '3': 'Map 3',
        '4': 'Map 4',
        '5': 'Map 5'
    }
    return period_names.get(str(period), f'Map {period}')

def is_prop_bet(team1, team2):
    """Check if this is a prop bet (Yes/No, Odd/Even, etc.)"""
    prop_indicators = ['Yes', 'No', 'Odd', 'Even', 'By']
    return any(indicator in team1 or indicator in team2 for indicator in prop_indicators)

def is_score_scenario(team1, team2):
    """Check if this is a score scenario bet (e.g., 'Team 0, Team 2 vs Team 1, Team 2')"""
    return ',' in team1 or ',' in team2

def is_expired_match(matchup_data):
    """Check if the match is expired or inactive"""
    if not matchup_data:
        return True
    # Check if the match has a start time and if it's in the past
    start_time = matchup_data.get('startTime')
    if start_time:
        try:
            match_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            return match_time < datetime.now(match_time.tzinfo)
        except:
            return True
    return False

def get_all_leagues(headers):
    """Fetch all available leagues from Pinnacle API"""
    url = 'https://guest.api.arcadia.pinnacle.se/0.1/leagues'
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except:
        return []

def is_cs_league(league):
    """Check if the league is a CS:GO/CS2 league"""
    name = league.get('name', '').lower()
    return 'counter-strike' in name or 'cs:' in name or 'cs ' in name

def get_cs_leagues(headers):
    """Try different methods to find CS:GO leagues"""
    # Known CS:GO league IDs
    known_league_ids = [
        263392,  # Current working league
        12,      # Esports league
        263393,  # Another potential CS:GO league
        263394,  # Another potential CS:GO league
    ]
    
    leagues = []
    for league_id in known_league_ids:
        url = f'https://guest.api.arcadia.pinnacle.se/0.1/leagues/{league_id}'
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            league_data = response.json()
            if league_data:
                leagues.append(league_data)
        except:
            continue
    
    return leagues

def main():
    headers = {
        'sec-ch-ua-platform': 'macOS',
        'X-Device-UUID': DEVICE_UUID,
        'Referer': 'https://www.pinnacle.se/',
        'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        'X-API-Key': X_API_KEY,
        'sec-ch-ua-mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    try:
        # Get all CS:GO matches from the sports endpoint
        url = 'https://guest.api.arcadia.pinnacle.se/0.1/sports/12/markets/straight?primaryOnly=false&withSpecials=false'
        print(f"\nFetching all CS:GO matches...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Group markets by matchupId
        markets_by_matchup = {}
        for market in data:
            matchup_id = market.get('matchupId')
            if matchup_id not in markets_by_matchup:
                markets_by_matchup[matchup_id] = []
            markets_by_matchup[matchup_id].append(market)
        
        print(f"Found {len(markets_by_matchup)} matches")
        
        # Process each matchup
        for matchup_id, markets in markets_by_matchup.items():
            # Get matchup details
            matchup_url = f'https://guest.api.arcadia.pinnacle.se/0.1/matchups/{matchup_id}'
            matchup_response = requests.get(matchup_url, headers=headers)
            matchup_data = matchup_response.json()
            
            # Get team names
            home_team = "Home"
            away_team = "Away"
            if matchup_data and 'participants' in matchup_data:
                participants = matchup_data['participants']
                if len(participants) >= 2:
                    home_team = participants[0].get('name', 'Home')
                    away_team = participants[1].get('name', 'Away')
            
            # Skip prop bets, score scenarios, and expired matches
            if (is_prop_bet(home_team, away_team) or 
                is_score_scenario(home_team, away_team) or 
                is_expired_match(matchup_data)):
                continue
            
            print(f"\nEvent: {home_team} vs {away_team}")
            print("-" * 50)
            
            # Group markets by period
            markets_by_period = {}
            for market in markets:
                period = market.get('period')
                if period not in markets_by_period:
                    markets_by_period[period] = []
                markets_by_period[period].append(market)
            
            # Print markets for each period
            for period, period_markets in sorted(markets_by_period.items()):
                period_name = get_period_name(period)
                print(f"\n{period_name} Markets:")
                print("-" * 30)
                
                # Print moneyline first
                moneylines = [m for m in period_markets if m['type'] == 'moneyline']
                for ml in moneylines:
                    home_odds = format_price(ml['prices'][0]['price'])
                    away_odds = format_price(ml['prices'][1]['price'])
                    print(f"{period_name} Winner")
                    print(f"  {home_team}: {home_odds}")
                    print(f"  {away_team}: {away_odds}")
                
                # Print spreads
                spreads = [m for m in period_markets if m['type'] == 'spread']
                for spread in spreads:
                    for price in spread['prices']:
                        team = home_team if price['designation'] == 'home' else away_team
                        points = price['points']
                        odds = format_price(price['price'])
                        sign = '+' if points > 0 else ''
                        if period == '0':
                            print(f"{team} {sign}{points} ({odds})")
                        else:
                            print(f"{period_name} - {team} {sign}{points} ({odds})")
                
                # Print totals
                totals = [m for m in period_markets if m['type'] == 'total']
                for total in totals:
                    points = total['prices'][0]['points']
                    over_odds = format_price(total['prices'][0]['price'])
                    under_odds = format_price(total['prices'][1]['price'])
                    if period == '0':
                        print(f"Total Maps {points} (Over {over_odds}/Under {under_odds})")
                    else:
                        print(f"{period_name} - Total Rounds {points} (Over {over_odds}/Under {under_odds})")
                
                print("-" * 30)
        
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
