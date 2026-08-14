import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Settings:
    """Configuración centralizada de la aplicación."""
    
    # API Keys
    THE_STATS_API_KEY: str = os.getenv("THE_STATS_API_KEY", "")
    ODDS_API_KEY: str = os.getenv("ODDS_API_KEY", "")
    
    # Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")
    
    # Kelly Criterion
    KELLY_FRACTION: float = 0.25
    MIN_STAKE: int = 1
    MAX_STAKE: int = 10
    
    # Thresholds
    MIN_EV_PERCENT: float = 5.0  # Mínimo 5% EV para notificar
    MIN_PROBABILITY: float = 30.0  # Mínimo 30% probabilidad
    
    # Rate Limiting
    API_RATE_LIMIT_DELAY: float = 1.0  # Segundos entre requests
    
    # Web Server
    FLASK_HOST: str = "0.0.0.0"
    FLASK_PORT: int = 5000
    FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    
    def validate(self) -> bool:
        """Valida que las configuraciones críticas estén presentes."""
        if not self.THE_STATS_API_KEY:
            print("⚠️ WARNING: THE_STATS_API_KEY no configurada")
            return False
        if not self.ODDS_API_KEY:
            print("⚠️ WARNING: ODDS_API_KEY no configurada")
            return False
        return True

settings = Settings()
