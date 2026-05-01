from __future__ import annotations
import pandas as pd
from loguru import logger
from app.strategies.base import BaseStrategy
from app.analysis.technical.indicators import TechnicalIndicators
from app.analysis.technical.support_resistance import SupportResistanceAnalyzer
from app.config import get_settings


class CryptoSpotStrategy(BaseStrategy):
    name = "crypto_spot"
    asset_types = ["crypto"]
    timeframes = ["4h", "1d"]

    def __init__(self):
        self.weight = get_settings().STRATEGY_CRYPTO_WEIGHT

    async def generate_signal(self, symbol: str, df: pd.DataFrame, context: dict) -> dict | None:
        if len(df) < 35:
            return None
        try:
            ti = TechnicalIndicators()
            analysis = ti.analyze(df)
            if "error" in analysis:
                return None

            current_price = float(df["close"].iloc[-1])
            rsi = analysis["rsi_value"]
            macd_signal = analysis["macd_signal"]
            ema200 = float(ti.ema(df, 200).iloc[-1]) if len(df) >= 200 else float(ti.ema(df, 50).iloc[-1])
            above_ema200 = current_price > ema200

            sr = SupportResistanceAnalyzer()
            stop_long = sr.calculate_stop_loss(df, current_price, "long", 2.0)
            target_long = sr.calculate_target(df, current_price, "long", 2.0)

            if rsi < 40 and macd_signal == "bullish" and above_ema200:
                confidence = 0.65
                return self._build_signal(
                    symbol=symbol, asset_type="crypto",
                    signal_type="buy", strength=0.7, confidence=confidence,
                    entry_price=current_price, target_price=target_long, stop_loss=stop_long,
                    reasoning=f"Crypto spot buy: RSI={rsi:.1f} oversold, MACD bullish, above EMA200",
                    timeframe=context.get("timeframe", "4h"),
                    crypto_specific={"exchange": "binance", "is_spot": True},
                )

            if rsi > 70 and macd_signal == "bearish":
                stop_short = sr.calculate_stop_loss(df, current_price, "short", 2.0)
                target_short = sr.calculate_target(df, current_price, "short", 2.0)
                return self._build_signal(
                    symbol=symbol, asset_type="crypto",
                    signal_type="sell", strength=0.65, confidence=0.60,
                    entry_price=current_price, target_price=target_short, stop_loss=stop_short,
                    reasoning=f"Crypto spot sell: RSI={rsi:.1f} overbought, MACD bearish",
                    timeframe=context.get("timeframe", "4h"),
                    crypto_specific={"exchange": "binance", "is_spot": True},
                )
            return None
        except Exception as e:
            logger.warning(f"CryptoSpotStrategy error for {symbol}: {e}")
            return None
