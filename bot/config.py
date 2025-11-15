"""
Configuration for Telegram bot.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Bot settings."""
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # Backend API
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "backend")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    
    # Strategy parameters (for display only)
    TIMEFRAME: str = os.getenv("TIMEFRAME", "1h")
    RISK_PER_TRADE: float = float(os.getenv("RISK_PER_TRADE", "2.0"))
    MAX_OPEN_POSITIONS: int = int(os.getenv("MAX_OPEN_POSITIONS", "1"))
    RR_RATIO: float = float(os.getenv("RR_RATIO", "2.5"))


settings = Settings()
