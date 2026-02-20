import requests
from datetime import datetime
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
import json

@dataclass
class Team:
    id: int
    name: str
    hasImage: bool

@dataclass
class Selection:
    id: int
    name: str
    status: int
    odds: float
    handicap: Optional[float]
    total: Optional[str]
    type: str

@dataclass
class Period:
    type: str
    number: Optional[int]

@dataclass
class BasicMarket:
    id: int
    name: str
    type: int
    status: int
    home: Dict
    away: Dict
    draw: Optional[Dict]
    hasCombo: bool
    hasInPlay: bool
    order: int
    overrideMainOrder: bool
    isSgc: bool

    @classmethod
    def from_dict(cls, data: Optional[Dict]) -> Optional['BasicMarket']:
        if data is None:
            return None
        return cls(**data)

@dataclass
class DetailedMarket:
    eventId: int
    id: int
    name: str
    status: int
    type: int
    category: int
    selections: List[Selection]
    order: int
    hasCombo: bool
    hasInPlay: bool
    isVisible: bool
    overrideMainOrder: bool
    handicap: Optional[float]
    baseLine: Optional[str]
    isMainLine: bool
    lineMarketColumnNames: Optional[Dict]
    customColumnNames: Optional[Dict]
    subCategory: int
    isFeatured: bool
    period: Optional[Period]
    isSgc: bool

    @classmethod
    def from_dict(cls, data: Dict) -> 'DetailedMarket':
        selections = [Selection(**s) for s in data.get('selections', [])]
        period = Period(**data['period']) if data.get('period') else None
        return cls(
            eventId=data['eventId'],
            id=data['id'],
            name=data['name'],
            status=data['status'],
            type=data['type'],
            category=data['category'],
            selections=selections,
            order=data['order'],
            hasCombo=data['hasCombo'],
            hasInPlay=data['hasInPlay'],
            isVisible=data['isVisible'],
            overrideMainOrder=data['overrideMainOrder'],
            handicap=data.get('handicap'),
            baseLine=data.get('baseLine'),
            isMainLine=data['isMainLine'],
            lineMarketColumnNames=data.get('lineMarketColumnNames'),
            customColumnNames=data.get('customColumnNames'),
            subCategory=data['subCategory'],
            isFeatured=data['isFeatured'],
            period=period,
            isSgc=data['isSgc']
        )

@dataclass
class Competition:
    id: int
    name: str
    shortName: str
    countryCode: Optional[str]
    defaultStream: Optional[str]

@dataclass
class Match:
    id: int
    gameId: int
    startTime: datetime
    name: str
    isLive: bool
    teams: Dict[str, Team]
    competition: Competition
    market: Optional[BasicMarket] = None
    totalOpenMarkets: Optional[int] = None
    totalAvailableMarkets: Optional[int] = None
    bestOf: Optional[int] = None
    hasInPlayMarkets: Optional[bool] = None
    isHighlighted: Optional[bool] = None
    isLiveModeOverridden: Optional[bool] = None
    hasMainMarket: Optional[bool] = None
    sgcEnabled: Optional[bool] = None

class ThunderpickScraper:
    BASE_URL = "https://thunderpick.io/api"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Cache-Control": "no-cache, no-store, max-age=0, must-revalidate",
            "Referer": "https://thunderpick.io/esports",
            "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "Content-Type": "application/json"
        })

    def get_matches(self) -> List[Match]:
        """Fetch all matches from Thunderpick API."""
        payload = {
            "gameIds": [1,2,3,4,6,7,8,9,19,20,21,23,32,34,35,38,39,40,41,42,49,50,51],
            "competitionId": None,
            "country": None
        }

        response = self.session.post(f"{self.BASE_URL}/matches", json=payload)
        response.raise_for_status()

        if not response.text.strip():
            raise Exception("Empty response received from Thunderpick API")

        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print(f"Could not parse JSON! Response was:\n{response.text[:500]}")
            raise e

        if not data.get("ok"):
            raise Exception("Failed to fetch matches from Thunderpick")

        matches = []
        match_list = data["data"].get("matches", []) or data["data"].get("upcoming", [])

        for match_data in match_list:
            match = self._parse_match(match_data)
            matches.append(match)

        return matches

    def _parse_match(self, data: Dict) -> Match:
        """Parse raw match data into Match object."""
        match_data = {
            "id": data["id"],
            "gameId": data["gameId"],
            "startTime": datetime.fromisoformat(data["startTime"].replace("Z", "+00:00")),
            "name": data["name"],
            "isLive": data["isLive"],
            "teams": {
                "home": Team(**data["teams"]["home"]),
                "away": Team(**data["teams"]["away"])
            },
            "competition": Competition(**data["competition"]),
            "market": BasicMarket.from_dict(data.get("market"))
        }
        
        optional_fields = [
            "totalOpenMarkets", "totalAvailableMarkets", "bestOf",
            "hasInPlayMarkets", "isHighlighted", "isLiveModeOverridden",
            "hasMainMarket", "sgcEnabled"
        ]
        
        for field in optional_fields:
            if field in data:
                match_data[field] = data[field]
                
        return Match(**match_data)

    def get_match_markets(self, match_id: int) -> List[DetailedMarket]:
        """Get all available markets for a specific match."""
        response = self.session.get(f"{self.BASE_URL}/markets/{match_id}")
        response.raise_for_status()
        data = response.json()
        
        if not data.get("ok"):
            raise Exception(f"Failed to fetch markets for match {match_id}")
            
        return [DetailedMarket.from_dict(market_data) for market_data in data.get("data", [])]

if __name__ == "__main__":
    scraper = ThunderpickScraper()
    matches = scraper.get_matches()
    for match in matches:
        print(f"\n{match.name} - {match.startTime}")
        print(f"Home: {match.teams['home'].name}")
        print(f"Away: {match.teams['away'].name}")
        
        try:
            markets = scraper.get_match_markets(match.id)
            print("\nAvailable markets:")
            for market in markets:
                print(f"\n{market.name}:")
                for selection in market.selections:
                    odds_str = f" ({selection.odds})" if selection.odds else ""
                    handicap_str = f" [H: {selection.handicap}]" if selection.handicap is not None else ""
                    total_str = f" [T: {selection.total}]" if selection.total else ""
                    print(f"  {selection.name}{odds_str}{handicap_str}{total_str}")
        except Exception as e:
            print(f"Error fetching markets: {e}")
        print("\n" + "-"*50) 