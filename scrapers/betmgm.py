import requests
from datetime import datetime
import json

def format_price(price):
    """Convert American odds to decimal odds"""
    if price > 0:
        return round((price / 100) + 1, 2)
    else:
        return round((100 / abs(price)) + 1, 2)

def format_odds(odds):
    """Convert odds from API format to decimal odds"""
    return round(odds / 1000, 2)

def format_handicap(line):
    """Format handicap line to show correct value"""
    # The line values are in thousandths, so we need to divide by 1000
    # and round to 1 decimal place
    return round(line / 1000, 1)

def get_event_markets(event_id: int) -> dict:
    """Fetch all markets for a specific event"""
    url = f'https://eu1.offering-api.kambicdn.com/offering/v2018/betmgmse/betoffer/event/{event_id}.json'
    params = {
        'lang': 'sv_SE',
        'market': 'SE',
        'client_id': '2',
        'channel_id': '1',
        'includeParticipants': 'true'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'sv-SE,sv;q=0.9,en-US;q=0.8,en;q=0.7',
        'Origin': 'https://www.betmgm.se',
        'Referer': 'https://www.betmgm.se/'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching markets for event {event_id}: {e}")
        return None

def get_esports_events():
    """Fetch esports events from BetMGM API"""
    url = 'https://www.betmgm.se/api/lmbas'
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # First, visit the main page to get necessary cookies
    main_page_url = 'https://www.betmgm.se/sport'
    session.get(main_page_url)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Content-Type': 'application/json',
        'Origin': 'https://www.betmgm.se',
        'Referer': 'https://www.betmgm.se/sport',
        'x-app-id': 'sportsbook',
        'x-app-version': '2.194.0',
        'x-client-id': 'sportsbook',
        'x-client-version': '2.194.0',
        'x-kambi-env': 'C3',
        'Accept-Language': 'sv-SE,sv;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin'
    }
    
    # The exact query from the website
    query = """query SportLeaguesQuery($market: String!, $lang: String!, $offering: String!, $filter: SportsEventsFilter, $grouping: [SportsEventsGrouping!], $first: Int, $after: String, $pageRequest: PageRequest, $allFilter: SportsEventsFilter, $allGrouping: [SportsEventsGrouping!], $skipAllLeaguesSportsQuery: Boolean, $skipPopularLeaguesSportsQuery: Boolean, $skipAllOutrightsSportsQuery: Boolean, $popularEventsGroup: [String!], $variant: String) {
        viewer {
            sports {
                sportsEvents(market: $market, lang: $lang, offering: $offering, filter: $filter, grouping: $grouping, first: $first, after: $after, pageRequest: $pageRequest, allFilter: $allFilter, allGrouping: $allGrouping, skipAllLeaguesSportsQuery: $skipAllLeaguesSportsQuery, skipPopularLeaguesSportsQuery: $skipPopularLeaguesSportsQuery, skipAllOutrightsSportsQuery: $skipAllOutrightsSportsQuery, popularEventsGroup: $popularEventsGroup, variant: $variant) {
                    groups {
                        __typename
                        id
                        name
                        englishName
                        termKey
                        groups {
                            __typename
                            id
                            name
                            englishName
                            termKey
                            events {
                                id
                                start
                                tags
                                name
                                nameDelimiter
                                englishName
                                state
                                liveData {
                                    statistics
                                    matchClock {
                                        period
                                        running
                                    }
                                    score {
                                        home
                                        away
                                        info
                                    }
                                }
                                betOffers {
                                    id
                                    eventId
                                    tags
                                    suspended
                                    criterion {
                                        label
                                    }
                                    outcomes {
                                        id
                                        odds
                                        oddsFractional
                                        label
                                        line
                                        englishLabel
                                        participant
                                        type
                                        betOfferId
                                        participantId
                                        oddsAmerican
                                        status
                                        cashOutStatus
                                    }
                                }
                                homeName
                                awayName
                                nonLiveBoCount
                                liveBoCount
                                sport
                                path {
                                    termKey
                                }
                                participants {
                                    participantId
                                    name
                                    home
                                }
                                metaData
                            }
                        }
                    }
                }
            }
        }
    }"""
    
    # Properly format the GraphQL request with variables
    payload = {
        "operationName": "SportLeaguesQuery",
        "variables": {
            "market": "SE",
            "lang": "sv_SE",
            "offering": "betmgmse",
            "filter": {
                "sport": "esports",
                "upcomingDays": 2,
                "eventType": "MATCH"
            },
            "grouping": ["LEAGUE_POPULARITY", "COUNTRY_AZ"],
            "first": 10,
            "after": "0",
            "pageRequest": {
                "pageNumber": 0,
                "pageSize": 5
            },
            "allFilter": {
                "sport": "esports",
                "upcomingDays": 20,
                "eventType": "MATCH"
            },
            "allGrouping": ["COUNTRY_AZ", "LEAGUE_POPULARITY"],
            "skipAllLeaguesSportsQuery": False,
            "skipPopularLeaguesSportsQuery": False,
            "skipAllOutrightsSportsQuery": True,
            "popularEventsGroup": [],
            "variant": "default"
        },
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "2880618e832c9648047bd384237a25ca0711ac5d8a171476bf565b2a6b115472"
            }
        }
    }
    
    try:
        response = session.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching events: {e}")
        return None

def translate_market_name(name):
    """Translate Swedish market names to English"""
    translations = {
        "Karta": "Map",
        "Totala": "Total",
        "Först": "First",
        "Första": "First",
        "Båda": "Both",
        "Flest": "Most",
        "Korrekt": "Correct",
        "Över": "Over",
        "Under": "Under",
        "Ja": "Yes",
        "Nej": "No",
        "Jämnt": "Even",
        "Udda": "Odd",
        "Rundhandikapp": "Round Handicap",
        "Karthandikapp": "Map Handicap",
        "Matchodds": "Match Winner",
        "Totala kartor": "Total Maps",
        "Totala rundor": "Total Rounds",
        "Totala Kills": "Total Kills",
        "Totala minuter": "Total Minutes",
        "Totala antalet": "Total Number of",
        "Totala slaktade drakar": "Total Dragons Killed",
        "Totala antalet dräpta Baroner": "Total Barons Killed",
        "Totala antalet förstörda Kanontorn": "Total Turrets Destroyed",
        "Totala antalet Champion Kills": "Total Champion Kills",
        "Först till": "First to",
        "Första blodet": "First Blood",
        "Först att döda en baron": "First to Kill a Baron",
        "Första lag som förstör en inhibitor": "First Team to Destroy an Inhibitor",
        "Första draktyp att bli dödad": "First Dragon Type to be Killed",
        "Båda lagen dräper en baron": "Both Teams Kill a Baron",
        "Båda lagen förstör en inhibitor": "Both Teams Destroy an Inhibitor",
        "Båda lagen dödar en drake": "Both Teams Kill a Dragon",
        "går till förlängning": "Goes to Overtime",
        "Runda": "Round",
        "Champion Kills Handicap": "Champion Kills Handicap"
    }
    
    for swedish, english in translations.items():
        name = name.replace(swedish, english)
    return name

def display_events(data):
    """Display events in a readable format"""
    if not data or 'data' not in data:
        print("No data available")
        return
    
    try:
        sport_events = data['data']['viewer']['sports']['sportsEvents']
        if not sport_events or 'groups' not in sport_events:
            print("No events found in the response")
            return
            
        print("\n=== Upcoming and Live Matches ===\n")
        
        for group in sport_events['groups']:
            if not group or 'groups' not in group:
                continue
                
            for sub_group in group['groups']:
                if not sub_group or 'events' not in sub_group:
                    continue
                    
                # Print the tournament/league name
                print(f"\n{'-' * 50}")
                print(f"Tournament: {sub_group['name']}")
                print(f"{'-' * 50}")
                    
                for event in sub_group['events']:
                    if not event:
                        continue
                        
                    # Format the time
                    start_time = datetime.fromtimestamp(int(event['start'])/1000)
                    time_str = start_time.strftime("%Y-%m-%d %H:%M")
                    
                    # Print the match info
                    print(f"\n{event['name']}")
                    print(f"Time: {time_str}")
                    print(f"Status: {event['state']}")
                    
                    if event['liveData'] and event['liveData']['score']:
                        score = event['liveData']['score']
                        print(f"Score: {score['home']} - {score['away']}")
                        if score['info']:
                            print(f"Info: {score['info']}")
                    
                    # Fetch and display detailed markets
                    markets_data = get_event_markets(event['id'])
                    if markets_data and 'betOffers' in markets_data:
                        print("\nAvailable markets:")
                        for market in markets_data['betOffers']:
                            if market.get('criterion', {}).get('label'):
                                market_name = market['criterion'].get('englishLabel', market['criterion']['label'])
                                print(f"\n{market_name}:")
                                for outcome in market.get('outcomes', []):
                                    if outcome['status'] == 'OPEN':
                                        line_info = f" [Line: {format_handicap(outcome['line'])}]" if outcome.get('line') else ""
                                        outcome_label = outcome.get('englishLabel', outcome['label'])
                                        print(f"  {outcome_label}: {format_odds(outcome['odds'])}{line_info}")
                    else:
                        print("\nNo additional markets available")
                    
    except KeyError as e:
        print(f"Error accessing data structure: {e}")
        return

def main():
    data = get_esports_events()
    if data:
        display_events(data)

if __name__ == "__main__":
    main() 