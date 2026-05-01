from __future__ import annotations
import pandas as pd
from loguru import logger
from app.strategies.base import BaseStrategy
from app.analysis.technical.indicators import TechnicalIndicators
from app.analysis.technical.support_resistance import SupportResistanceAnalyzer
from app.config import get_settings


class MomentumStrategy(BaseStrategy):
    name = "momentum"
    asset_types = ["stock", "crypto"]
    timeframes = ["1h", "4h", "1d"]

    def __init__(self):
        settings = get_settings()
        self.weight = settings.STRATEGY_MOMENTUM_WEIGHT

    async def generate_signal(self, symbol: str, df: pd.DataFrame, context: dict) -> dict | None:
        if len(df) < 35:
            return None
        try:
            ti = TechnicalIndicators()
            analysis = ti.analyze(df)
            if "error" in analysis:
                return None

            current_price = float(df["close"].iloc[-1])
            avg_volume = float(df["volume"].rolling(20).mean().iloc[-1]) if "volume" in df.columns else 1.0
            current_volume = float(df["volume"].iloc[-1]) if "volume" in df.columns else 1.0
            volume_surge = current_volume > avg_volume * 1.5

            ema20 = float(ti.ema(df, 20).iloc[-1])
            rsi = analysis["rsi_value"]
            macd_signal = analysis["macd_signal"]

            sr = SupportResistanceAnalyzer()
            levels = sr.find_levels(df)
            support = levels["support"]
            resistance = levels["resistance"]
            stop = sr.calculate_stop_loss(df, current_price, "long")
            target = sr.calculate_target(df, current_price, "long")

            buy_conditions = [
                40 <= rsi <= 65,
                macd_signal == "bullish",
                volume_surge,
                current_price > ema20,
            ]
            sell_conditions = [
                rsi > 70,
                macd_signal == "bearish",
                current_price < ema20,
            ]

            buy_score = sum(buy_conditions)
            sell_score = sum(sell_conditions)

            if buy_score >= 3:
                strength = min(1.0, buy_score / 4 + (0.1 if volume_surge else 0))
                confidence = min(0.9, buy_score * 0.22)
                sentiment = context.get("sentiment", {})
                if sentiment.get("score", 0) > 0:
                    confidence = min(0.95, confidence + 0.05)
                return self._build_signal(
                    symbol=symbol, asset_type=context.get("asset_type", "stock"),
                    signal_type="buy", strength=strength, confidence=confidence,
                    entry_price=current_price, target_price=target, stop_loss=stop,
                    reasoning=f"Momentum buy: RSI={rsi:.1f}, MACD={macd_signal}, volume_surge={volume_surge}, price>EMA20",
                    timeframe=context.get("timeframe", "1d"),
                )

            if sell_score >= 2:
                stop_short = sr.calculate_stop_loss(df, current_price, "short")
                target_short = sr.calculate_target(df, current_price, "short")
                confidence = min(0.85, sell_score * 0.27)
                return self._build_signal(
                    symbol=symbol, asset_type=context.get("asset_type", "stock"),
                    signal_type="sell", strength=sell_score / 3, confidence=confidence,
                    entry_price=current_price, target_price=target_short, stop_loss=stop_short,
                    reasoning=f"Momentum sell: RSI={rsi:.1f}, MACD={macd_signal}",
                    timeframe=context.get("timeframe", "1d"),
                )
            return None
        except Exception as e:
            logger.warning(f"MomentumStrategy error for {symbol}: {e}")
            return None
