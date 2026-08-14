import os
import requests
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from config.settings import settings

class APIClientBase:
    """Clase base para clientes API con manejo de errores y rate limiting."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Implementa rate limiting entre requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < settings.API_RATE_LIMIT_DELAY:
            time.sleep(settings.API_RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict = None, headers: Dict = None) -> Optional[Dict]:
        """Realiza una petición HTTP con manejo de errores."""
        self._rate_limit()
        
        try:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error {e.response.status_code}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Request Error: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
            return None


class StatsAPIClient(APIClientBase):
    """Cliente para TheStatsAPI - Estadísticas de partidos."""
    
    def __init__(self):
        super().__init__("https://thestatsapi.com/api/football")
        self.api_key = settings.THE_STATS_API_KEY
        self.headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
    
    def get_matches_by_date(self, date_str: str) -> List[Dict]:
        """
        Obtiene partidos por fecha.
        
        Args:
            date_str: Fecha en formato YYYY-MM-DD
            
        Returns:
            Lista de partidos con sus datos
        """
        data = self._make_request("matches", params={"date": date_str}, headers=self.headers)
        return data.get("data", []) if data else []
    
    def get_match_stats(self, match_id: str) -> Optional[Dict]:
        """
        Obtiene estadísticas detalladas de un partido.
        
        Args:
            match_id: ID del partido
            
        Returns:
            Diccionario con estadísticas del partido
        """
        data = self._make_request(f"matches/{match_id}/stats", headers=self.headers)
        return data.get("data") if data else None
    
    def get_team_stats(self, team_id: str, season: str = None) -> Optional[Dict]:
        """
        Obtiene estadísticas de un equipo.
        
        Args:
            team_id: ID del equipo
            season: Temporada (opcional)
            
        Returns:
            Diccionario con estadísticas del equipo
        """
        params = {"season": season} if season else {}
        data = self._make_request(f"teams/{team_id}/stats", params=params, headers=self.headers)
        return data.get("data") if data else None
    
    def get_team_form(self, team_id: str, limit: int = 5) -> List[Dict]:
        """
        Obtiene los últimos resultados de un equipo.
        
        Args:
            team_id: ID del equipo
            limit: Número de partidos recientes
            
        Returns:
            Lista de últimos partidos
        """
        data = self._make_request(f"teams/{team_id}/matches", 
                                  params={"limit": limit}, 
                                  headers=self.headers)
        return data.get("data", []) if data else []


class OddsAPIClient(APIClientBase):
    """Cliente para The Odds API - Cuotas de casas de apuestas."""
    
    def __init__(self):
        super().__init__("https://api.the-odds-api.com/v4/sports")
        self.api_key = settings.ODDS_API_KEY
    
    def get_odds(self, 
                 sport_key: str = "soccer_spain_la_liga",
                 regions: str = "eu",
                 markets: str = "h2h,totals",
                 odds_format: str = "decimal") -> List[Dict]:
        """
        Obtiene cuotas de mercado para una liga específica.
        
        Args:
            sport_key: Clave de la liga (ej: soccer_epl)
            regions: Regiones de casas de apuestas (eu, us, uk, au)
            markets: Mercados (h2h, spreads, totals)
            odds_format: Formato de cuotas (decimal, american)
            
        Returns:
            Lista de partidos con sus cuotas
        """
        params = {
            "apiKey": self.api_key,
            "regions": regions,
            "markets": markets,
            "oddsFormat": odds_format
        }
        
        data = self._make_request(f"{sport_key}/odds", params=params)
        return data if data and isinstance(data, list) else []
    
    def get_available_sports(self) -> List[Dict]:
        """
        Obtiene lista de deportes/ligas disponibles.
        
        Returns:
            Lista de deportes disponibles
        """
        data = self._make_request("", params={"apiKey": self.api_key})
        return data if data and isinstance(data, list) else []
    
    def get_remaining_requests(self) -> Optional[int]:
        """
        Verifica cuántas requests quedan en el límite de la API.
        
        Returns:
            Número de requests restantes
        """
        response = requests.get(
            f"{self.base_url}",
            params={"apiKey": self.api_key}
        )
        return int(response.headers.get("x-requests-remaining", 0))


class APIClientsManager:
    """Manager centralizado para todos los clientes API."""
    
    def __init__(self):
        self.stats_client = StatsAPIClient()
        self.odds_client = OddsAPIClient()
        
    def validate_clients(self) -> bool:
        """Valida que los clientes estén correctamente configurados."""
        if not settings.THE_STATS_API_KEY:
            print("❌ THE_STATS_API_KEY no configurada")
            return False
        if not settings.ODDS_API_KEY:
            print("❌ ODDS_API_KEY no configurada")
            return False
        return True
    
    def get_stats_client(self) -> StatsAPIClient:
        return self.stats_client
    
    def get_odds_client(self) -> OddsAPIClient:
        return self.odds_client
