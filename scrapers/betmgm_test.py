import requests
from datetime import datetime
import json

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
        print("Making request to BetMGM API...")
        print(f"Request URL: {url}")
        print(f"Request headers: {json.dumps(headers, indent=2)}")
        print(f"Request payload: {json.dumps(payload, indent=2)}")
        
        response = session.post(url, headers=headers, json=payload)
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")
        
        if response.status_code != 200:
            print(f"Error response: {response.text}")
            return None
            
        data = response.json()
        print("Successfully received response")
        print(f"Full response: {json.dumps(data, indent=2)}")
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        print(f"Response content: {e.response.text if hasattr(e, 'response') else 'No response content'}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        print(f"Raw response: {response.text}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

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
            
        print("\n=== API Response Structure Analysis ===\n")
        
        # Print available fields in the response
        print("Available fields in sportsEvents:")
        for key in sport_events.keys():
            print(f"- {key}")
            
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
                    print(f"Total Betting Offers: {event['nonLiveBoCount']}")
                    
                    # Print all available fields in the event
                    print("\nAvailable fields in event:")
                    for key in event.keys():
                        print(f"- {key}")
                    
                    if event['liveData'] and event['liveData']['score']:
                        score = event['liveData']['score']
                        print(f"Score: {score['home']} - {score['away']}")
                        if score['info']:
                            print(f"Info: {score['info']}")
                    
                    # Get all betting markets
                    markets = {}
                    print("\nAvailable Betting Markets:")
                    for offer in event['betOffers']:
                        market_type = offer['criterion']['label']
                        print(f"\nMarket Type: {market_type}")
                        print("Market Details:")
                        print(f"- ID: {offer['id']}")
                        print(f"- Tags: {offer.get('tags', [])}")
                        print(f"- Suspended: {offer.get('suspended')}")
                        print("Criterion Details:")
                        for key, value in offer['criterion'].items():
                            print(f"  - {key}: {value}")
                        print("Outcomes:")
                        for outcome in offer['outcomes']:
                            print(f"  - {outcome['label']}:")
                            for key, value in outcome.items():
                                if key not in ['label', 'id']:
                                    print(f"    {key}: {value}")
                        
                        if market_type not in markets:
                            markets[market_type] = []
                            
                        market_odds = {}
                        for outcome in offer['outcomes']:
                            if outcome['status'] == 'OPEN':
                                market_odds[outcome['label']] = {
                                    'decimal': outcome['odds'] / 1000 if outcome['odds'] else None,
                                    'american': outcome['oddsAmerican'],
                                    'line': outcome.get('line'),
                                    'type': outcome.get('type'),
                                    'tags': offer.get('tags', [])
                                }
                        markets[market_type].append(market_odds)
                    
                    # Print all betting markets with details
                    for market_type, market_odds_list in markets.items():
                        print(f"\n{market_type}:")
                        for market_odds in market_odds_list:
                            for team, odds in market_odds.items():
                                line_info = f" ({odds['line']})" if odds['line'] else ""
                                type_info = f" [{odds['type']}]" if odds['type'] else ""
                                tags_info = f" {odds['tags']}" if odds['tags'] else ""
                                print(f"  {team}{line_info}{type_info}{tags_info}: {odds['decimal']} ({odds['american']})")
                    
    except KeyError as e:
        print(f"Error accessing data structure: {e}")
        print(f"Available keys in data: {data.keys() if isinstance(data, dict) else 'Not a dictionary'}")
        if isinstance(data, dict) and 'data' in data:
            print(f"Available keys in data['data']: {data['data'].keys()}")
        return

def main():
    data = get_esports_events()
    if data:
        display_events(data)

if __name__ == "__main__":
    main() 