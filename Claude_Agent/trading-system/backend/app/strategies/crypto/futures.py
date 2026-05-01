from __future__ import annotations
import pandas as pd
from loguru import logger
from app.strategies.crypto.spot import CryptoSpotStrategy
from app.analysis.technical.indicators import TechnicalIndicators
from app.analysis.technical.support_resistance import SupportResistanceAnalyzer


class CryptoFuturesStrategy(CryptoSpotStrategy):
    name = "crypto_futures"
    MAX_LEVERAGE = 3
    DEFAULT_LEVERAGE = 2

    async def generate_signal(self, symbol: str, df: pd.DataFrame, context: dict) -> dict | None:
        base = await super().generate_signal(symbol, df, context)
        if base is None:
            return None

        if base["confidence"] < 0.75:
            return None

        funding_rate = context.get("funding_rate", 0.0)
        confidence = base["confidence"]
        if funding_rate > 0.01 and base["signal_type"] == "buy":
            confidence = max(0.0, confidence - 0.1)

        leverage = self.DEFAULT_LEVERAGE
        entry = base["entry_price"]
        liquidation_price = round(entry - (entry / leverage), 4) if base["signal_type"] == "buy" else round(entry + (entry / leverage), 4)

        base.update({
            "asset_type": "crypto_futures",
            "confidence": round(confidence, 3),
            "leverage": leverage,
            "liquidation_price": liquidation_price,
            "funding_rate": funding_rate,
            "crypto_specific": {"exchange": "binance", "is_spot": False, "leverage": leverage},
            "strategy_name": self.name,
        })
        return base
