from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core infrastructure
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _coerce_db_url(cls, v: str) -> str:
        # Railway managed PostgreSQL provides postgresql:// or postgres://
        # SQLAlchemy asyncpg driver requires postgresql+asyncpg://
        if isinstance(v, str):
            if v.startswith("postgres://"):
                v = "postgresql+asyncpg://" + v[len("postgres://"):]
            elif v.startswith("postgresql://"):
                v = "postgresql+asyncpg://" + v[len("postgresql://"):]
        return v

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

    # Binance / Binance US
    BINANCE_API_KEY: str = ""
    BINANCE_API_SECRET: str = ""
    BINANCE_TESTNET: bool = True
    CRYPTO_EXCHANGE: str = "binanceus"  # "binanceus" (default) or "binance" for non-US

    # Coinbase
    COINBASE_API_KEY: str = ""
    COINBASE_API_SECRET: str = ""

    # Weex (crypto derivatives exchange — https://www.weex.com)
    WEEX_API_KEY: str = ""
    WEEX_API_SECRET: str = ""
    WEEX_PASSPHRASE: str = ""        # required by Weex; set in API management

    # Interactive Brokers (TWS / IB Gateway must be running locally)
    IB_HOST: str = "127.0.0.1"
    IB_PORT: int = 7497              # 7497=TWS paper | 7496=TWS live | 4002=Gateway paper | 4001=Gateway live
    IB_CLIENT_ID: int = 1
    IB_ACCOUNT: str = ""             # leave blank to use the primary account

    # Strategy allocation weights
    STRATEGY_MOMENTUM_WEIGHT: float = 0.25
    STRATEGY_SWING_WEIGHT: float = 0.25
    STRATEGY_MEAN_REVERSION_WEIGHT: float = 0.20
    STRATEGY_OPTIONS_WEIGHT: float = 0.15
    STRATEGY_CRYPTO_WEIGHT: float = 0.15

    # ML model paths (Phase 2)
    MODEL_DIR: str = "models"                     # directory for all trained model files
    META_MODEL_MIN_CONFIDENCE: float = 0.55       # below this → HOLD (don't trade)
    META_MODEL_FORWARD_BARS: int = 5              # forward-return label horizon (bars)
    REGIME_N_STATES: int = 6                      # number of HMM hidden states


@lru_cache
def get_settings() -> Settings:
    return Settings()
