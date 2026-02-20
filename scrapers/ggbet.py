import json
import asyncio
import aiohttp
import websockets
import websockets.extensions.permessage_deflate
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class Team:
    id: str
    name: str
    logo: Optional[str]
    home_away: str

@dataclass
class Tournament:
    id: str
    name: str
    country_code: str
    start_date: datetime
    end_date: datetime
    logo: Optional[str]

@dataclass
class Market:
    id: str
    name: str
    type_id: int
    status: str
    odds: List['Odd']
    specifiers: List[Dict[str, str]]

@dataclass
class Odd:
    id: str
    name: str
    value: float
    is_active: bool
    status: str
    competitor_ids: List[str]

@dataclass
class Match:
    id: str
    title: str
    start_time: datetime
    status: str
    home_team: Team
    away_team: Team
    tournament: Tournament
    markets: List[Market]
    score: str
    best_of: Optional[int]

class GGBetScraper:
    WS_URL = "wss://gg-b-gql.gg.bet/graphql"
    API_URL = "https://api.gg.bet"
    
    def __init__(self):
        self.session = None
        self.ws = None
        self.subscription_id = None
        self.matches: Dict[str, Match] = {}
        self.auth_token = None

    async def get_auth_token(self):
        """Get authentication token from GG.bet API."""
        try:
            url = f"{self.API_URL}/auth/anonymous"
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Origin": "https://gg.bet",
                "Referer": "https://gg.bet/",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            }
            
            payload = {
                "deviceId": "web",
                "deviceType": "web",
                "platform": "web"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.auth_token = result.get("token")
                        if not self.auth_token:
                            raise Exception("No token in response")
                        print("Successfully obtained auth token")
                    else:
                        error_text = await response.text()
                        raise Exception(f"Failed to get auth token: {response.status}, {error_text}")
        except Exception as e:
            print(f"Error getting auth token: {e}")
            raise

    async def connect(self):
        """Connect to GG.bet WebSocket"""
        try:
            # First get the auth token
            await self.get_auth_token()
            
            headers = {
                'Host': 'gg-b-gql.gg.bet',
                'Origin': 'https://gg.bet',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Upgrade': 'websocket',
                'Connection': 'Upgrade',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': '*/*',
                'Sec-Fetch-Site': 'same-site',
                'Sec-Fetch-Mode': 'websocket',
                'Sec-Fetch-Dest': 'websocket',
                'Sec-WebSocket-Protocol': 'graphql-ws'
            }
            
            self.ws = await websockets.connect(
                self.WS_URL,
                additional_headers=headers,
                subprotocols=['graphql-ws'],
                compression=None
            )
            print("Connected to GG.bet WebSocket")
            
            # Send connection init message with auth token
            await self.ws.send(json.dumps({
                'type': 'connection_init',
                'payload': {
                    'headers': {
                        'Authorization': f'Bearer {self.auth_token}'
                    }
                }
            }))
            
            # Wait for connection acknowledgment
            response = await self.ws.recv()
            print(f"Connection response: {response}")
            
            # Subscribe to matches
            await self.subscribe_to_matches()
            
        except Exception as e:
            print(f"Error connecting to WebSocket: {e}")
            raise

    async def subscribe_to_matches(self):
        """Subscribe to esports matches via GraphQL subscription"""
        subscribe_message = {
            "id": "1",
            "type": "subscribe",
            "payload": {
                "query": """
                subscription {
                    matches {
                        id
                        status
                        startAt
                        game {
                            id
                            name
                            slug
                        }
                        tournament {
                            id
                            name
                            slug
                        }
                        teams {
                            id
                            name
                            logo
                        }
                        markets {
                            id
                            name
                            status
                            odds {
                                id
                                name
                                value
                                status
                            }
                        }
                    }
                }
                """,
                "variables": {}
            }
        }
        
        await self.ws.send(json.dumps(subscribe_message))
        print("Subscribed to esports matches")

    def _parse_match(self, event_data: Dict) -> Match:
        """Parse raw match data into Match object"""
        fixture = event_data['fixture']
        competitors = fixture['competitors']
        
        # Find home and away teams
        home_team_data = next(c for c in competitors if c['homeAway'] == 'HOME')
        away_team_data = next(c for c in competitors if c['homeAway'] == 'AWAY')
        
        home_team = Team(
            id=home_team_data['id'],
            name=home_team_data['name'],
            logo=home_team_data.get('logo'),
            home_away=home_team_data['homeAway']
        )
        
        away_team = Team(
            id=away_team_data['id'],
            name=away_team_data['name'],
            logo=away_team_data.get('logo'),
            home_away=away_team_data['homeAway']
        )
        
        tournament_data = fixture['tournament']
        tournament = Tournament(
            id=tournament_data['id'],
            name=tournament_data['name'],
            country_code=tournament_data['countryCode'],
            start_date=datetime.fromisoformat(tournament_data['dateStart'].replace('Z', '+00:00')),
            end_date=datetime.fromisoformat(tournament_data['dateEnd'].replace('Z', '+00:00')),
            logo=tournament_data.get('logo')
        )
        
        # Parse markets
        markets = []
        for market_data in event_data.get('markets', []):
            odds = [
                Odd(
                    id=odd['id'],
                    name=odd['name'],
                    value=float(odd['value']),
                    is_active=odd['isActive'],
                    status=odd['status'],
                    competitor_ids=odd.get('competitorIds', [])
                )
                for odd in market_data['odds']
            ]
            
            market = Market(
                id=market_data['id'],
                name=market_data['name'],
                type_id=market_data['typeId'],
                status=market_data['status'],
                odds=odds,
                specifiers=[{"name": s['name'], "value": s['value']} for s in market_data.get('specifiers', [])]
            )
            markets.append(market)
        
        # Get best_of from meta
        best_of = None
        for meta in event_data.get('meta', []):
            if meta['name'] == 'bo':
                best_of = int(meta['value'])
                break
        
        return Match(
            id=event_data['id'],
            title=fixture['title'],
            start_time=datetime.fromisoformat(fixture['startTime'].replace('Z', '+00:00')),
            status=fixture['status'],
            home_team=home_team,
            away_team=away_team,
            tournament=tournament,
            markets=markets,
            score=fixture['score'],
            best_of=best_of
        )

    async def listen_for_updates(self):
        """Listen for WebSocket updates"""
        try:
            while True:
                message = await self.ws.recv()
                data = json.loads(message)
                
                if data.get("type") == "connection_error":
                    print(f"Connection error: {data.get('payload', {}).get('message')}")
                    break
                elif data.get("type") == "next":
                    # Handle match data
                    match_data = data.get("payload", {}).get("data", {}).get("matches")
                    if match_data:
                        print(f"Received match update: {match_data}")
                elif data.get("type") == "error":
                    print(f"Subscription error: {data.get('payload')}")
                    break
                elif data.get("type") == "complete":
                    print("Subscription completed")
                    break
                
        except Exception as e:
            print(f"Error while listening for updates: {e}")
            raise

    async def cleanup(self):
        """Clean up resources"""
        if self.ws:
            await self.ws.close()
        if self.session:
            await self.session.close()

    async def run(self):
        """Main method to run the scraper"""
        try:
            await self.connect()
            await self.listen_for_updates()
        except Exception as e:
            print(f"Error running scraper: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.cleanup()

if __name__ == "__main__":
    scraper = GGBetScraper()
    asyncio.run(scraper.run()) 