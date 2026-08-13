import os
import requests

class StatsAPIClient:
    """Cliente para interactuar con TheStatsAPI (Estadísticas de córners, remates y eventos)."""
    BASE_URL = "https://thestatsapi.com/api/football"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("THE_STATS_API_KEY", "")
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    def get_matches_by_date(self, date_str: str):
        """GET /api/football/matches?date=YYYY-MM-DD"""
        response = requests.get(f"{self.BASE_URL}/matches", headers=self.headers, params={"date": date_str})
        response.raise_for_status()
        return response.json()

    def get_match_stats(self, match_id: str):
        """GET /api/football/matches/{match_id}/stats"""
        response = requests.get(f"{self.BASE_URL}/matches/{match_id}/stats", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_team_stats(self, team_id: str):
        """GET /api/football/teams/{team_id}/stats"""
        response = requests.get(f"{self.BASE_URL}/teams/{team_id}/stats", headers=self.headers)
        response.raise_for_status()
        return response.json()


class OddsAPIClient:
    """Cliente para interactuar con The Odds API (Cuotas de casas de apuestas)."""
    BASE_URL = "https://api.the-odds-api.com/v4/sports"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ODDS_API_KEY", "")

    def get_odds(self, sport_key: str = "soccer_spain_la_liga", regions: str = "eu", markets: str = "h2h,totals"):
        """GET /v4/sports/{sport_key}/odds"""
        params = {
            "apiKey": self.api_key,
            "regions": regions,
            "markets": markets,
            "oddsFormat": "decimal"
        }
        response = requests.get(f"{self.BASE_URL}/{sport_key}/odds", params=params)
        response.raise_for_status()
        return response.json()
