import numpy as np
from src.api.clients import StatsAPIClient, OddsAPIClient
from src.notifications.telegram_bot import TelegramNotifier

class ValueEngine:
    """Motor cuantitativo para la selección de cuotas con EV+."""
    
    def __init__(self):
        self.stats_client = StatsAPIClient()
        self.odds_client = OddsAPIClient()
        self.notifier = TelegramNotifier()

    @staticmethod
    def calculate_expected_value(real_prob: float, odds: float) -> float:
        """EV = (Probabilidad Real * Cuota) - 1"""
        return round(((real_prob / 100.0) * odds - 1) * 100, 2)

    @staticmethod
    def calculate_kelly_stake(real_prob: float, odds: float, bankroll_fraction: float = 0.25) -> int:
        """Criterio de Kelly fraccionado escalado a Stake 1-10."""
        p = real_prob / 100.0
        q = 1.0 - p
        b = odds - 1.0
        
        kelly = (b * p - q) / b
        if kelly <= 0:
            return 0
        
        stake = int(np.ceil(kelly * bankroll_fraction * 100))
        return min(max(stake, 1), 10)

    def process_match(self, match: str, league: str, market: str, stat_prob: float, current_odds: float):
        ev = self.calculate_expected_value(stat_prob, current_odds)
        
        # Filtro estricto: Solo valor esperable superior al 3%
        if ev > 3.0:
            stake = self.calculate_kelly_stake(stat_prob, current_odds)
            
            # Notificación directa a Telegram
            self.notifier.send_pick(
                match=match,
                league=league,
                market=market,
                stat_prob=stat_prob,
                odds=current_odds,
                ev=ev,
                stake=stake
            )

    def run_pipeline(self):
        print("Ejecutando motor cuantitativo...")
        # Lógica de escaneo diario cargando datos de las APIs
        # Ejemplo ejecutable de prueba de canalización:
        sample_candidates = [
            {
                "match": "Real Madrid vs Barcelona",
                "league": "LaLiga",
                "market": "Over 9.5 Córners",
                "stat_prob": 75.0,
                "odds": 1.50
            }
        ]

        for item in sample_candidates:
            self.process_match(
                match=item["match"],
                league=item["league"],
                market=item["market"],
                stat_prob=item["stat_prob"],
                current_odds=item["odds"]
            )

if __name__ == "__main__":
    engine = ValueEngine()
    engine.run_pipeline()
