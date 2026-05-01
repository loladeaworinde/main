from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal

router = APIRouter(prefix="/settings", tags=["settings"])


class ModeUpdate(BaseModel):
    mode: Literal["paper", "live"]


@router.post("/mode")
async def set_trading_mode(update: ModeUpdate):
    # In production this would update a persistent config store.
    # For now, return the requested mode with a warning for live.
    if update.mode == "live":
        return {
            "mode": "live",
            "warning": "Live trading will execute real orders with real money. Ensure all broker credentials are configured and tested.",
            "status": "mode_change_requires_restart",
        }
    return {"mode": "paper", "status": "ok"}


@router.get("/risk")
async def get_risk_settings():
    from app.config import get_settings
    settings = get_settings()
    return {
        "max_portfolio_heat": settings.MAX_PORTFOLIO_HEAT,
        "max_position_size": settings.MAX_POSITION_SIZE,
        "max_daily_loss": settings.MAX_DAILY_LOSS,
        "max_drawdown": settings.MAX_DRAWDOWN,
        "kelly_fraction": settings.KELLY_FRACTION,
        "trading_mode": settings.TRADING_MODE,
        "paper_starting_capital": settings.PAPER_STARTING_CAPITAL,
    }


@router.get("/strategy-weights")
async def get_strategy_weights():
    from app.config import get_settings
    settings = get_settings()
    return {
        "momentum": settings.STRATEGY_MOMENTUM_WEIGHT,
        "swing": settings.STRATEGY_SWING_WEIGHT,
        "mean_reversion": settings.STRATEGY_MEAN_REVERSION_WEIGHT,
        "options": settings.STRATEGY_OPTIONS_WEIGHT,
        "crypto": settings.STRATEGY_CRYPTO_WEIGHT,
    }


@router.get("/providers")
async def get_provider_status():
    from app.config import get_settings
    settings = get_settings()
    return {
        "polygon": bool(settings.POLYGON_API_KEY),
        "alpha_vantage": bool(settings.ALPHA_VANTAGE_KEY),
        "finnhub": bool(settings.FINNHUB_API_KEY),
        "news_api": bool(settings.NEWS_API_KEY),
        "reddit": bool(settings.REDDIT_CLIENT_ID),
        "anthropic": bool(settings.ANTHROPIC_API_KEY),
    }


@router.get("/brokers")
async def get_broker_status():
    from app.config import get_settings
    settings = get_settings()
    return {
        "robinhood": {"configured": bool(settings.ROBINHOOD_USERNAME), "status": "disconnected"},
        "webull": {"configured": bool(settings.WEBULL_USERNAME), "status": "disconnected"},
        "alpaca": {"configured": bool(settings.ALPACA_API_KEY), "status": "disconnected"},
        "binance": {"configured": bool(settings.BINANCE_API_KEY), "status": "disconnected", "testnet": settings.BINANCE_TESTNET},
    }
