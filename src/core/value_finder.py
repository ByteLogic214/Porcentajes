import os
import json
import time
import numpy as np
from datetime import datetime
from src.api.clients import StatsAPIClient, OddsAPIClient
from src.notifications.telegram_bot import TelegramNotifier
from config import settings

class ValueEngine:
    """Motor cuantitativo para análisis masivo de múltiples ligas simultáneas."""
    
    def __init__(self):
        self.stats_client = StatsAPIClient()
        self.odds_client = OddsAPIClient()
        self.notifier = TelegramNotifier()
        self.leagues = self._load_leagues()

    @staticmethod
    def _load_leagues():
        config_path = os.path.join(os.path.dirname(__file__), "../../config/leagues.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    @staticmethod
    def calculate_expected_value(real_prob: float, odds: float) -> float:
        """EV = (Probabilidad Real * Cuota) - 1"""
        return round(((real_prob / 100.0) * odds - 1) * 100, 2)

    @staticmethod
    def calculate_kelly_stake(real_prob: float, odds: float, bankroll_fraction: float = settings.KELLY_FRACTION) -> int:
        """Criterio de Kelly fraccionado escalado a Stake 1-10."""
        p = real_prob / 100.0
        q = 1.0 - p
        b = odds - 1.0
        
        kelly = (b * p - q) / b
        if kelly <= 0:
            return 0
        
        stake = int(np.ceil(kelly * bankroll_fraction * 100))
        return min(max(stake, settings.MIN_STAKE), settings.MAX_STAKE)

    def process_league(self, league_info: dict, target_date: str):
        league_name = league_info["league_name"]
        odds_key = league_info["odds_api_sport_key"]
        comp_id = league_info["stats_api_competition_id"]
        
        print(f"--- Procesando: {league_name} ---")
        
        try:
            # 1. Obtener cuotas del mercado para esta liga
            odds_data = self.odds_client.get_odds(sport_key=odds_key)
            if not odds_data:
                print(f"Sin cuotas disponibles para {league_name}")
                return

            # 2. Obtener fixture/partidos de TheStatsAPI
            matches_data = self.stats_client.get_matches_by_date(target_date)
            
            # TODO: Lógica de cruce de nombres de equipos entre ambas APIs
            # Y cálculo probabilístico sobre remates/córners/goles
            
        except Exception as e:
            print(f"Error procesando {league_name}: {e}")

    def run_pipeline(self):
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        print(f"Iniciando escaneo multiliga para la fecha: {today_str}")
        print(f"Ligas configuradas: {len(self.leagues)}")

        for league in self.leagues:
            self.process_league(league, today_str)
            time.sleep(1) # Previene bloqueos por límite de peticiones (Rate Limit)

        print("Pipeline finalizado con éxito.")

if __name__ == "__main__":
    engine = ValueEngine()
    engine.run_pipeline()
