from dataclasses import dataclass

@dataclass
class Settings:
    # Kelly criterion settings
    KELLY_FRACTION: float = 0.25  # 25% of bankroll per bet
    MIN_STAKE: int = 1
    MAX_STAKE: int = 10

settings = Settings()
