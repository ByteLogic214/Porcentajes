import numpy as np
from typing import Dict, Optional, Tuple
from config.settings import settings

class ValueCalculator:
    """Cálculos cuantitativos para Expected Value y Kelly Criterion."""
    
    @staticmethod
    def calculate_expected_value(real_probability: float, decimal_odds: float) -> float:
        """
        Calcula el Expected Value (EV).
        
        Formula: EV = (Probabilidad Real * Cuota) - 1
        
        Args:
            real_probability: Probabilidad real en porcentaje (0-100)
            decimal_odds: Cuota decimal de la casa de apuestas
            
        Returns:
            EV en porcentaje
        """
        if real_probability <= 0 or decimal_odds <= 1:
            return -100.0
        
        prob_decimal = real_probability / 100.0
        ev = (prob_decimal * decimal_odds - 1) * 100
        return round(ev, 2)
    
    @staticmethod
    def calculate_kelly_stake(real_probability: float, 
                            decimal_odds: float,
                            bankroll_fraction: float = None) -> int:
        """
        Calcula el stake óptimo usando Kelly Criterion fraccionado.
        
        Formula: Kelly = (bp - q) / b
        Donde:
            b = odds - 1 (ganancia neta por unidad apostada)
            p = probabilidad de ganar
            q = probabilidad de perder (1 - p)
        
        Args:
            real_probability: Probabilidad real en porcentaje (0-100)
            decimal_odds: Cuota decimal
            bankroll_fraction: Fracción del bankroll (default: KELLY_FRACTION)
            
        Returns:
            Stake entre MIN_STAKE y MAX_STAKE
        """
        if bankroll_fraction is None:
            bankroll_fraction = settings.KELLY_FRACTION
        
        p = real_probability / 100.0
        q = 1.0 - p
        b = decimal_odds - 1.0
        
        if b <= 0 or p <= 0:
            return 0
        
        kelly = (b * p - q) / b
        
        if kelly <= 0:
            return 0
        
        # Escalar a stake 1-10
        fractional_kelly = kelly * bankroll_fraction
        stake = int(np.ceil(fractional_kelly * 100))
        
        return min(max(stake, settings.MIN_STAKE), settings.MAX_STAKE)
    
    @staticmethod
    def calculate_implied_probability(decimal_odds: float) -> float:
        """
        Calcula la probabilidad implícita de las cuotas.
        
        Formula: Probabilidad = (1 / Cuota) * 100
        
        Args:
            decimal_odds: Cuota decimal
            
        Returns:
            Probabilidad implícita en porcentaje
        """
        if decimal_odds <= 0:
            return 0.0
        return round((1 / decimal_odds) * 100, 2)
    
    @staticmethod
    def calculate_margin(odds_list: list) -> float:
        """
        Calcula el margen (overround) de la casa de apuestas.
        
        Args:
            odds_list: Lista de cuotas decimales de todos los resultados posibles
            
        Returns:
            Margen en porcentaje
        """
        if not odds_list:
            return 0.0
        
        total_prob = sum(1 / odds for odds in odds_list if odds > 0)
        margin = (total_prob - 1) * 100
        return round(margin, 2)


class StatisticalAnalyzer:
    """Análisis estadístico de equipos y partidos."""
    
    @staticmethod
    def calculate_team_performance_score(team_stats: Dict) -> float:
        """
        Calcula un score de rendimiento basado en estadísticas del equipo.
        
        Args:
            team_stats: Diccionario con estadísticas del equipo
            
        Returns:
            Score de rendimiento (0-100)
        """
        if not team_stats:
            return 50.0
        
        # Extraer métricas clave
        goals_scored = team_stats.get("goals_scored", 0)
        goals_conceded = team_stats.get("goals_conceded", 0)
        shots_per_game = team_stats.get("shots_per_game", 0)
        shots_on_target = team_stats.get("shots_on_target_per_game", 0)
        possession = team_stats.get("possession_avg", 50)
        
        # Normalizar y ponderar
        attack_score = min((goals_scored / 2) * 20, 30)
        defense_score = max(30 - (goals_conceded / 2) * 20, 0)
        efficiency_score = min((shots_on_target / shots_per_game) * 20, 20) if shots_per_game > 0 else 10
        control_score = (possession / 100) * 20
        
        total_score = attack_score + defense_score + efficiency_score + control_score
        return round(min(total_score, 100), 2)
    
    @staticmethod
    def calculate_match_probability(home_stats: Dict, away_stats: Dict) -> Tuple[float, float, float]:
        """
        Calcula probabilidades de victoria local, empate y victoria visitante.
        
        Args:
            home_stats: Estadísticas del equipo local
            away_stats: Estadísticas del equipo visitante
            
        Returns:
            Tupla (prob_home, prob_draw, prob_away) en porcentaje
        """
        home_score = StatisticalAnalyzer.calculate_team_performance_score(home_stats)
        away_score = StatisticalAnalyzer.calculate_team_performance_score(away_stats)
        
        # Ventaja de local (+10%)
        home_score += 10
        
        total = home_score + away_score
        
        if total == 0:
            return (33.33, 33.33, 33.33)
        
        prob_home = (home_score / total) * 70  # 70% se distribuye entre local y visitante
        prob_away = (away_score / total) * 70
        prob_draw = 30  # 30% base para empate
        
        # Normalizar a 100%
        total_prob = prob_home + prob_away + prob_draw
        prob_home = (prob_home / total_prob) * 100
        prob_away = (prob_away / total_prob) * 100
        prob_draw = (prob_draw / total_prob) * 100
        
        return (round(prob_home, 2), round(prob_draw, 2), round(prob_away, 2))
