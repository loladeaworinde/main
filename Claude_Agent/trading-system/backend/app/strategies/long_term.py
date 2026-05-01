from __future__ import annotations
import pandas as pd
from loguru import logger
from app.strategies.base import BaseStrategy
from app.analysis.technical.indicators import TechnicalIndicators
from app.config import get_settings


class LongTermStrategy(BaseStrategy):
    name = "long_term"
    asset_types = ["stock"]
    timeframes = ["1w", "1d"]

    def __init__(self):
        self.weight = get_settings().STRATEGY_SWING_WEIGHT * 0.8

    async def generate_signal(self, symbol: str, df: pd.DataFrame, context: dict) -> dict | None:
        if len(df) < 210:
            return None
        try:
            ti = TechnicalIndicators()
            ema50 = ti.ema(df, 50)
            sma200 = ti.sma(df, 200)
            current_price = float(df["close"].iloc[-1])
            current_sma200 = float(sma200.iloc[-1])
            current_ema50 = float(ema50.iloc[-1])

            uptrend = current_price > current_sma200
            pullback_to_ema50 = abs(current_price - current_ema50) / current_ema50 < 0.05

            sentiment = context.get("sentiment", {})
            sentiment_ok = sentiment.get("score", 0) > 0.1

            if uptrend and pullback_to_ema50 and sentiment_ok:
                stop = current_sma200 * 0.97
                target = current_price * 1.20
                confidence = 0.60 if sentiment_ok else 0.45
                return self._build_signal(
                    symbol=symbol, asset_type="stock",
                    signal_type="buy", strength=0.5, confidence=confidence,
                    entry_price=current_price, target_price=target, stop_loss=stop,
                    reasoning=f"Long-term buy: price above 200SMA, pullback to EMA50, positive sentiment",
                    timeframe="long_term",
                    scale_in=True,
                )

            below_sma200_streak = int((df["close"].tail(15) < sma200.tail(15)).sum())
            if below_sma200_streak >= 10:
                return self._build_signal(
                    symbol=symbol, asset_type="stock",
                    signal_type="sell", strength=0.7, confidence=0.70,
                    entry_price=current_price, target_price=current_price * 0.90, stop_loss=current_price * 1.05,
                    reasoning=f"Long-term sell: price broke below 200SMA for {below_sma200_streak} of last 15 periods",
                    timeframe="long_term",
                )
            return None
        except Exception as e:
            logger.warning(f"LongTermStrategy error for {symbol}: {e}")
            return None
