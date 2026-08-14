from difflib import SequenceMatcher
from typing import Optional, List, Dict
import re

class TeamNameMatcher:
    """Matcher para relacionar nombres de equipos entre diferentes APIs."""
    
    # Diccionario de nombres conocidos entre APIs
    TEAM_ALIASES = {
        "Manchester United": ["Man United", "Man Utd", "MUFC"],
        "Manchester City": ["Man City", "MCFC"],
        "Tottenham Hotspur": ["Tottenham", "Spurs"],
        "Newcastle United": ["Newcastle"],
        "West Ham United": ["West Ham"],
        "Brighton & Hove Albion": ["Brighton"],
        "Wolverhampton Wanderers": ["Wolves", "Wolverhampton"],
        "Nottingham Forest": ["Nott'm Forest"],
        "Borussia Dortmund": ["Dortmund", "BVB"],
        "Bayern Munich": ["Bayern München", "Bayern"],
        "Atletico Madrid": ["Atlético Madrid", "Atletico"],
        "Athletic Bilbao": ["Athletic Club"],
        "Paris Saint Germain": ["PSG", "Paris SG"],
        "Inter Milan": ["Internazionale", "Inter"],
        "AC Milan": ["Milan"],
    }
    
    @staticmethod
    def normalize_name(team_name: str) -> str:
        """
        Normaliza el nombre de un equipo eliminando caracteres especiales.
        
        Args:
            team_name: Nombre del equipo
            
        Returns:
            Nombre normalizado
        """
        # Eliminar caracteres especiales y convertir a minúsculas
        normalized = re.sub(r'[^\w\s]', '', team_name.lower())
        # Eliminar palabras comunes
        common_words = ['fc', 'cf', 'club', 'united', 'city', 'athletic']
        words = [w for w in normalized.split() if w not in common_words]
        return ' '.join(words)
    
    @staticmethod
    def similarity_score(name1: str, name2: str) -> float:
        """
        Calcula la similitud entre dos nombres de equipos.
        
        Args:
            name1: Primer nombre
            name2: Segundo nombre
            
        Returns:
            Score de similitud (0-1)
        """
        norm1 = TeamNameMatcher.normalize_name(name1)
        norm2 = TeamNameMatcher.normalize_name(name2)
        
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    @staticmethod
    def find_best_match(target_team: str, 
                       candidate_teams: List[str], 
                       threshold: float = 0.7) -> Optional[str]:
        """
        Encuentra el mejor match de un equipo en una lista de candidatos.
        
        Args:
            target_team: Nombre del equipo a buscar
            candidate_teams: Lista de equipos candidatos
            threshold: Umbral mínimo de similitud
            
        Returns:
            Mejor match o None si no hay match suficiente
        """
        # Primero buscar en aliases conocidos
        for canonical_name, aliases in TeamNameMatcher.TEAM_ALIASES.items():
            if target_team in [canonical_name] + aliases:
                for candidate in candidate_teams:
                    if candidate in [canonical_name] + aliases:
                        return candidate
        
        # Si no hay alias, buscar por similitud
        best_match = None
        best_score = 0
        
        for candidate in candidate_teams:
            score = TeamNameMatcher.similarity_score(target_team, candidate)
            if score > best_score and score >= threshold:
                best_score = score
                best_match = candidate
        
        return best_match
    
    @staticmethod
    def match_teams(stats_teams: Dict, odds_teams: Dict) -> Dict[str, str]:
        """
        Relaciona equipos entre dos fuentes de datos.
        
        Args:
            stats_teams: Diccionario {team_id: team_name} de StatsAPI
            odds_teams: Diccionario {team_id: team_name} de OddsAPI
            
        Returns:
            Diccionario {stats_team_id: odds_team_name}
        """
        matches = {}
        odds_team_names = list(odds_teams.values())
        
        for stats_id, stats_name in stats_teams.items():
            best_match = TeamNameMatcher.find_best_match(stats_name, odds_team_names)
            if best_match:
                matches[stats_id] = best_match
        
        return matches
