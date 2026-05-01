from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime, timezone
import pytz
from loguru import logger


EASTERN = pytz.timezone("America/New_York")


class BaseStrategy(ABC):
    name: str = "base"
    asset_types: list[str] = []
    timeframes: list[str] = ["1d"]
    weight: float = 0.2

    @abstractmethod
    async def generate_signal(self, symbol: str, df, context: dict) -> dict | None:
        ...

    async def validate_signal(self, signal: dict, risk_manager) -> bool:
        if not signal:
            return False
        required = ["symbol", "signal_type", "entry_price", "stop_loss"]
        return all(k in signal and signal[k] is not None for k in required)

    @staticmethod
    def is_market_hours() -> bool:
        now_et = datetime.now(EASTERN)
        if now_et.weekday() >= 5:
            return False
        market_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
        return market_open <= now_et <= market_close

    def _build_signal(self, symbol: str, asset_type: str, signal_type: str, strength: float, confidence: float,
                      entry_price: float, target_price: float, stop_loss: float, reasoning: str,
                      timeframe: str = "1d", **extra) -> dict:
        base = {
            "symbol": symbol,
            "asset_type": asset_type,
            "signal_type": signal_type,
            "strength": round(max(0.0, min(1.0, strength)), 3),
            "confidence": round(max(0.0, min(1.0, confidence)), 3),
            "entry_price": round(entry_price, 4),
            "target_price": round(target_price, 4),
            "stop_loss": round(stop_loss, 4),
            "reasoning": reasoning,
            "timeframe": timeframe,
            "strategy_name": self.name,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        base.update(extra)
        return base
