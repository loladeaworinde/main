from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core infrastructure
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str

    # Trading mode
    TRADING_MODE: Literal["paper", "live"] = "paper"

    # Risk management
    PAPER_STARTING_CAPITAL: float = 100_000.0
    MAX_PORTFOLIO_HEAT: float = 0.20
    MAX_POSITION_SIZE: float = 0.05
    MAX_DAILY_LOSS: float = 0.03
    MAX_DRAWDOWN: float = 0.15
    KELLY_FRACTION: float = 0.25

    # Market data providers
    POLYGON_API_KEY: str = ""
    ALPHA_VANTAGE_KEY: str = ""
    FINNHUB_API_KEY: str = ""
    NEWS_API_KEY: str = ""

    # Reddit sentiment
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT: str = ""

    # AI
    ANTHROPIC_API_KEY: str = ""

    # Robinhood
    ROBINHOOD_USERNAME: str = ""
    ROBINHOOD_PASSWORD: str = ""
    ROBINHOOD_TOTP_SECRET: str = ""

    # Webull
    WEBULL_USERNAME: str = ""
    WEBULL_PASSWORD: str = ""
    WEBULL_DEVICE_ID: str = ""
    WEBULL_TRADING_PIN: str = ""

    # Alpaca
    ALPACA_API_KEY: str = ""
    ALPACA_API_SECRET: str = ""
    ALPACA_BASE_URL: str = "https://paper-api.alpaca.markets"

    # Binance
    BINANCE_API_KEY: str = ""
    BINANCE_API_SECRET: str = ""
    BINANCE_TESTNET: bool = True

    # Coinbase
    COINBASE_API_KEY: str = ""
    COINBASE_API_SECRET: str = ""

    # Strategy allocation weights
    STRATEGY_MOMENTUM_WEIGHT: float = 0.25
    STRATEGY_SWING_WEIGHT: float = 0.25
    STRATEGY_MEAN_REVERSION_WEIGHT: float = 0.20
    STRATEGY_OPTIONS_WEIGHT: float = 0.15
    STRATEGY_CRYPTO_WEIGHT: float = 0.15


@lru_cache
def get_settings() -> Settings:
    return Settings()
