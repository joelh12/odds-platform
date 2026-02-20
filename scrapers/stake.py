import requests
import json
from datetime import datetime
from stake_auth import AuthClass

class StakeScraper:
    def __init__(self):
        self.session = requests.Session()
        self.ESPORTS_ID = "esports"

    def get_event_payload(self, live=False):
        """Generate the GraphQL query payload"""
        if live:
            return {
                "operationName": "liveSportFixtureList",
                "variables": {
                    "tournamentLimit": 50,
                    "sportId": self.ESPORTS_ID,
                    "groups": "winner"
                },
                "query": """
                query liveSportFixtureList($sportId: String!, $groups: String!, $tournamentLimit: Int = 25) {
                    sport(sportId: $sportId) {
                        id
                        tournamentList(type: live, limit: $tournamentLimit) {
                            id
                            name
                            fixtureList(type: live) {
                                id
                                status
                                data {
                                    startTime
                                    competitors {
                                        name
                                    }
                                }
                                groups(groups: [$groups], status: [active, suspended, deactivated]) {
                                    name
                                    markets {
                                        name
                                        outcomes {
                                            name
                                            odds
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                """
            }
        else:
            return {
                "operationName": "SportFixtureList",
                "variables": {
                    "type": "upcoming",
                    "sportId": self.ESPORTS_ID,
                    "groups": "winner",
                    "limit": 50,
                    "offset": 0
                },
                "query": """
                query SportFixtureList($type: SportSearchEnum!, $sportId: String!, $groups: String!, $limit: Int!, $offset: Int!) {
                    sport(sportId: $sportId) {
                        id
                        name
                        fixtureList(type: $type, limit: $limit, offset: $offset) {
                            id
                            status
                            data {
                                startTime
                                competitors {
                                    name
                                }
                            }
                            groups(groups: [$groups], status: [active, suspended, deactivated]) {
                                name
                                markets {
                                    name
                                    outcomes {
                                        name
                                        odds
                                    }
                                }
                            }
                        }
                    }
                }
                """
            }

    def scrape_events(self, live=False):
        """Fetch events from the API"""
        try:
            payload = self.get_event_payload(live)
            response = self.session.post(
                AuthClass.API_URL,
                headers=AuthClass.get_headers(),
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request: {e}")
            print("Response content:", response.text if 'response' in locals() else "No response content")
            return None

    def format_events(self, data):
        """Format the API response into a readable format"""
        if not data or 'data' not in data or 'sport' not in data['data']:
            print("No data found in response")
            return

        print(f"\nScraped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 50)

        sport = data['data']['sport']
        if 'tournamentList' in sport:  # Live events
            for tournament in sport['tournamentList']:
                print(f"\nTournament: {tournament.get('name', 'Unknown')}")
                print("-" * 30)
                for fixture in tournament.get('fixtureList', []):
                    self._print_fixture(fixture)
        elif 'fixtureList' in sport:  # Upcoming events
            for fixture in sport['fixtureList']:
                self._print_fixture(fixture)

    def _print_fixture(self, fixture):
        """Print details of a single fixture"""
        if not isinstance(fixture, dict):
            return

        try:
            if 'data' in fixture and 'competitors' in fixture['data']:
                competitors = fixture['data']['competitors']
                if len(competitors) >= 2:
                    home_team = competitors[0].get('name', 'Home')
                    away_team = competitors[1].get('name', 'Away')
                    print(f"\nMatch: {home_team} vs {away_team}")
                    print("-" * 30)

            if 'groups' in fixture:
                for group in fixture['groups']:
                    if 'markets' in group:
                        for market in group['markets']:
                            print(f"\nMarket: {market.get('name', 'Unknown')}")
                            for outcome in market.get('outcomes', []):
                                print(f"{outcome.get('name', 'Unknown')}: {outcome.get('odds', 'N/A')}")
        except Exception as e:
            print(f"Error printing fixture: {e}")

def main():
    scraper = StakeScraper()
    
    # Try both live and upcoming events
    print("Fetching live events...")
    live_data = scraper.scrape_events(live=True)
    scraper.format_events(live_data)
    
    print("\nFetching upcoming events...")
    upcoming_data = scraper.scrape_events(live=False)
    scraper.format_events(upcoming_data)

if __name__ == "__main__":
    main() 