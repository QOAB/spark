"""
Configuration management using Pydantic Settings.
Environment variables loaded from .env file.
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/trading_bot",
        description="PostgreSQL connection string"
    )
    
    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379",
        description="Redis connection string"
    )
    
    # Exchange API (Binance)
    EXCHANGE_API_KEY: str = Field(default="", description="Binance API Key")
    EXCHANGE_API_SECRET: str = Field(default="", description="Binance API Secret")
    EXCHANGE_TESTNET: bool = Field(default=True, description="Use testnet")
    
    # Capital and Risk Management
    INITIAL_CAPITAL: float = Field(default=500.0, description="Starting capital in USD")
    RISK_PER_TRADE: float = Field(default=2.0, description="Risk percentage per trade")
    MAX_OPEN_POSITIONS: int = Field(default=1, description="Maximum concurrent positions")
    DAILY_LOSS_LIMIT: float = Field(default=6.0, description="Daily loss limit percentage")
    
    # Strategy Parameters
    TIMEFRAME: str = Field(default="1h", description="Trading timeframe")
    EMA_FAST: int = Field(default=9, description="Fast EMA period")
    EMA_SLOW: int = Field(default=21, description="Slow EMA period")
    RSI_LENGTH: int = Field(default=14, description="RSI period")
    RSI_LONG_THRESHOLD: int = Field(default=50, description="RSI threshold for long entries")
    RSI_SHORT_THRESHOLD: int = Field(default=50, description="RSI threshold for short entries")
    LOOKBACK: int = Field(default=40, description="Breakout lookback period")
    ATR_LENGTH: int = Field(default=14, description="ATR period")
    RR_RATIO: float = Field(default=2.5, description="Risk/Reward ratio")
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = Field(default="", description="Telegram bot token")
    
    # Misc
    TIMEZONE: str = Field(default="Europe/Luxembourg", description="Timezone")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
