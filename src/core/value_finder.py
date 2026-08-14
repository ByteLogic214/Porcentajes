#!/usr/bin/env python3
"""
Value Finder Engine - Motor de análisis cuantitativo de value betting
Escanea múltiples ligas simultáneamente buscando oportunidades con EV+
"""

import os
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

from src.api.clients import APIClientsManager
from src.core.calculations import ValueCalculator, StatisticalAnalyzer
from src.core.team_matcher import TeamNameMatcher
from src.notifications.telegram_bot import TelegramNotifier
from config.settings import settings


@dataclass
class ValuePick:
    """Modelo de datos para una selección de apuesta con valor."""
    match_id: str
    match_name: str
    league: str
    market: str
    selection: str
    real_probability: float
    decimal_odds: float
    expected_value: float
    kelly_stake: int
    bookmaker: str
    match_time: str
    timestamp: str
    
    def to_dict(self) -> dict:
        return asdict(self)


class ValueEngine:
    """Motor cuantitativo para análisis masivo de múltiples ligas simultáneas."""
    
    def __init__(self):
        self.api_manager = APIClientsManager()
        self.stats_client = self.api_manager.get_stats_client()
        self.odds_client = self.api_manager.get_odds_client()
        self.notifier = TelegramNotifier()
        self.calculator = ValueCalculator()
        self.analyzer = StatisticalAnalyzer()
        self.team_matcher = TeamNameMatcher()
        
        self.leagues = self._load_leagues()
        self.value_picks: List[ValuePick] = []
        
        print("🚀 Value Engine inicializado")
        print(f"📊 Ligas configuradas: {len(self.leagues)}")
        print(f"📱 Telegram: {'✅ Configurado' if self.notifier.is_configured() else '❌ No configurado'}")
    
    @staticmethod
    def _load_leagues() -> List[Dict]:
        """Carga la configuración de ligas desde leagues.json"""
        config_path = os.path.join(os.path.dirname(__file__), "config/leagues.json")
        
        if not os.path.exists(config_path):
            print(f"⚠️ Archivo {config_path} no encontrado")
            return []
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                leagues = json.load(f)
                # Filtrar solo ligas activas
                return [l for l in leagues if l.get("enabled", True)]
        except Exception as e:
            print(f"❌ Error cargando leagues.json: {e}")
            return []
    
    def _find_value_in_match(self, 
                            match_odds: Dict,
                            match_stats: Optional[Dict]) -> List[ValuePick]:
        """
        Analiza un partido individual buscando oportunidades de valor.
        
        Args:
            match_odds: Datos de cuotas del partido
            match_stats: Estadísticas del partido (puede ser None)
            
        Returns:
            Lista de ValuePick encontrados
        """
        picks = []
        
        try:
            match_name = f"{match_odds['home_team']} vs {match_odds['away_team']}"
            match_time = match_odds.get("commence_time", "")
            
            # Si no hay stats, usar probabilidades básicas
            if not match_stats:
                # Probabilidades default basadas en odds implícitas
                home_prob = 40.0
                draw_prob = 30.0
                away_prob = 30.0
            else:
                # Calcular probabilidades basadas en estadísticas reales
                home_prob, draw_prob, away_prob = self.analyzer.calculate_match_probability(
                    match_stats.get("home", {}),
                    match_stats.get("away", {})
                )
            
            # Analizar cada bookmaker y mercado
            for bookmaker in match_odds.get("bookmakers", []):
                bookmaker_name = bookmaker.get("title", "Unknown")
                
                for market in bookmaker.get("markets", []):
                    market_key = market.get("key")
                    
                    # Mercado H2H (Home/Draw/Away)
                    if market_key == "h2h":
                        outcomes = {o["name"]: o["price"] for o in market.get("outcomes", [])}
                        
                        # Analizar Victoria Local
                        if match_odds["home_team"] in outcomes:
                            home_odds = outcomes[match_odds["home_team"]]
                            ev = self.calculator.calculate_expected_value(home_prob, home_odds)
                            
                            if ev >= settings.MIN_EV_PERCENT and home_prob >= settings.MIN_PROBABILITY:
                                stake = self.calculator.calculate_kelly_stake(home_prob, home_odds)
                                
                                pick = ValuePick(
                                    match_id=match_odds.get("id", ""),
                                    match_name=match_name,
                                    league=match_odds.get("sport_title", ""),
                                    market="Victoria Local",
                                    selection=match_odds["home_team"],
                                    real_probability=home_prob,
                                    decimal_odds=home_odds,
                                    expected_value=ev,
                                    kelly_stake=stake,
                                    bookmaker=bookmaker_name,
                                    match_time=match_time,
                                    timestamp=datetime.now().isoformat()
                                )
                                picks.append(pick)
                        
                        # Analizar Empate
                        if "Draw" in outcomes:
                            draw_odds = outcomes["Draw"]
                            ev = self.calculator.calculate_expected_value(draw_prob, draw_odds)
                            
                            if ev >= settings.MIN_EV_PERCENT and draw_prob >= settings.MIN_PROBABILITY:
                                stake = self.calculator.calculate_kelly_stake(draw_prob, draw_odds)
                                
                                pick = ValuePick(
                                    match_id=match_odds.get("id", ""),
                                    match_name=match_name,
                                    league=match_odds.get("sport_title", ""),
                                    market="Empate",
                                    selection="Draw",
                                    real_probability=draw_prob,
                                    decimal_odds=draw_odds,
                                    expected_value=ev,
                                    kelly_stake=stake,
                                    bookmaker=bookmaker_name,
                                    match_time=match_time,
                                    timestamp=datetime.now().isoformat()
                                )
                                picks.append(pick)
                        
                        # Analizar Victoria Visitante
                        if match_odds["away_team"] in outcomes:
                            away_odds = outcomes[match_odds["away_team"]]
                            ev = self.calculator.calculate_expected_value(away_prob, away_odds)
                            
                            if ev >= settings.MIN_EV_PERCENT and away_prob >= settings.MIN_PROBABILITY:
                                stake = self.calculator.calculate_kelly_stake(away_prob, away_odds)
                                
                                pick = ValuePick(
                                    match_id=match_odds.get("id", ""),
                                    match_name=match_name,
                                    league=match_odds.get("sport_title", ""),
                                    market="Victoria Visitante",
                                    selection=match_odds["away_team"],
                                    real_probability=away_prob,
                                    decimal_odds=away_odds,
                                    expected_value=ev,
                                    kelly_stake=stake,
                                    bookmaker=bookmaker_name,
                                    match_time=match_time,
                                    timestamp=datetime.now().isoformat()
                                )
                                picks.append(pick)
        
        except Exception as e:
            print(f"❌ Error analizando partido {match_name}: {e}")
        
        return picks
    
    def process_league(self, league_info: Dict, target_date: str) -> int:
        """
        Procesa una liga completa buscando value picks.
        
        Args:
            league_info: Información de la liga desde leagues.json
            target_date: Fecha objetivo en formato YYYY-MM-DD
            
        Returns:
            Número de picks encontrados
        """
        league_name = league_info["league_name"]
        odds_key = league_info["odds_api_sport_key"]
        
        print(f"\n{'='*60}")
        print(f"🔍 Analizando: {league_name}")
        print(f"{'='*60}")
        
        picks_found = 0
        
        try:
            # 1. Obtener cuotas de mercado
            print(f"📊 Obteniendo cuotas de mercado...")
            odds_data = self.odds_client.get_odds(sport_key=odds_key)
            
            if not odds_data:
                print(f"⚠️ No hay cuotas disponibles para {league_name}")
                return 0
            
            print(f"✅ {len(odds_data)} partidos con cuotas encontrados")
            
            # 2. Obtener estadísticas (opcional, puede fallar sin API key)
            print(f"📈 Obteniendo estadísticas...")
            matches_stats = {}
            
            try:
                stats_matches = self.stats_client.get_matches_by_date(target_date)
                if stats_matches:
                    print(f"✅ {len(stats_matches)} partidos con estadísticas")
                    for match in stats_matches:
                        match_id = match.get("id")
                        matches_stats[match_id] = match
            except Exception as e:
                print(f"⚠️ Stats API no disponible, usando probabilidades base: {e}")
            
            # 3. Analizar cada partido
            print(f"🔬 Analizando partidos en busca de valor...")
            
            for match_odds in odds_data:
                # Intentar encontrar stats del partido (matching por nombre)
                match_stats = None
                # TODO: Implementar matching más sofisticado con team_matcher
                
                # Buscar value en este partido
                picks = self._find_value_in_match(match_odds, match_stats)
                
                if picks:
                    picks_found += len(picks)
                    self.value_picks.extend(picks)
                    
                    # Notificar cada pick encontrado
                    for pick in picks:
                        print(f"\n🎯 VALUE PICK ENCONTRADO:")
                        print(f"   Partido: {pick.match_name}")
                        print(f"   Mercado: {pick.market} - {pick.selection}")
                        print(f"   Prob: {pick.real_probability}% | Cuota: {pick.decimal_odds}")
                        print(f"   EV: +{pick.expected_value}% | Stake: {pick.kelly_stake}/10")
                        
                        # Enviar a Telegram
                        self.notifier.send_pick(
                            match=pick.match_name,
                            league=pick.league,
                            market=pick.market,
                            stat_prob=pick.real_probability,
                            odds=pick.decimal_odds,
                            ev=pick.expected_value,
                            stake=pick.kelly_stake,
                            bookmaker=pick.bookmaker,
                            match_time=pick.match_time
                        )
            
            print(f"\n✅ Liga completada: {picks_found} picks con valor encontrados")
            
        except Exception as e:
            print(f"❌ Error procesando {league_name}: {e}")
            self.notifier.send_error(f"Error en {league_name}: {str(e)}")
        
        return picks_found
    
    def save_results(self):
        """Guarda los resultados del análisis en un archivo JSON."""
        if not self.value_picks:
            print("ℹ️ No hay picks para guardar")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"results/value_picks_{timestamp}.json"
        
        os.makedirs("results", exist_ok=True)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_picks": len(self.value_picks),
            "avg_ev": round(sum(p.expected_value for p in self.value_picks) / len(self.value_picks), 2),
            "picks": [pick.to_dict() for pick in self.value_picks]
        }
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Resultados guardados en: {filename}")
    
    def run_pipeline(self):
        """Ejecuta el pipeline completo de análisis."""
        start_time = time.time()
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        
        print("\n" + "="*60)
        print(f"🚀 VALUE BETTING ENGINE - INICIANDO ESCANEO")
        print("="*60)
        print(f"📅 Fecha: {today_str}")
        print(f"🏆 Ligas a analizar: {len(self.leagues)}")
        print(f"📊 EV mínimo: {settings.MIN_EV_PERCENT}%")
        print(f"🎯 Probabilidad mínima: {settings.MIN_PROBABILITY}%")
        print("="*60)
        
        # Validar configuración
        if not self.api_manager.validate_clients():
            print("\n❌ APIs no configuradas correctamente. Abortando.")
            return
        
        # Procesar cada liga
        total_picks = 0
        leagues_analyzed = 0
        
        for league in self.leagues:
            picks = self.process_league(league, today_str)
            total_picks += picks
            leagues_analyzed += 1
            
            # Rate limiting entre ligas
            time.sleep(settings.API_RATE_LIMIT_DELAY)
        
        # Resumen final
        elapsed_time = time.time() - start_time
        
        print("\n" + "="*60)
        print(f"✅ ESCANEO COMPLETADO")
        print("="*60)
        print(f"⏱️ Tiempo total: {elapsed_time:.2f} segundos")
        print(f"🏆 Ligas analizadas: {leagues_analyzed}")
        print(f"🎯 Total picks encontrados: {total_picks}")
        
        if self.value_picks:
            avg_ev = sum(p.expected_value for p in self.value_picks) / len(self.value_picks)
            best_pick = max(self.value_picks, key=lambda p: p.expected_value)
            
            print(f"📊 EV promedio: +{avg_ev:.2f}%")
            print(f"🏆 Mejor EV: +{best_pick.expected_value}% ({best_pick.match_name})")
            
            # Enviar resumen a Telegram
            self.notifier.send_daily_summary(
                total_picks=total_picks,
                leagues_analyzed=leagues_analyzed,
                avg_ev=avg_ev,
                best_pick=best_pick.to_dict()
            )
        
        # Guardar resultados
        self.save_results()
        
        print("="*60)


def main():
    """Función principal."""
    try:
        engine = ValueEngine()
        engine.run_pipeline()
    except KeyboardInterrupt:
        print("\n\n⚠️ Proceso interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        TelegramNotifier().send_error(f"Error crítico en Value Engine: {str(e)}")


if __name__ == "__main__":
    main()
