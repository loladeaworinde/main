from __future__ import annotations
import pandas as pd
from loguru import logger
from app.strategies.base import BaseStrategy
from app.analysis.technical.indicators import TechnicalIndicators
from app.analysis.technical.support_resistance import SupportResistanceAnalyzer
from app.config import get_settings


class SwingStrategy(BaseStrategy):
    name = "swing"
    asset_types = ["stock"]
    timeframes = ["1d"]

    def __init__(self):
        self.weight = get_settings().STRATEGY_SWING_WEIGHT

    def _is_hammer(self, df: pd.DataFrame) -> bool:
        c = df.iloc[-1]
        body = abs(c["close"] - c["open"])
        lower_wick = min(c["close"], c["open"]) - c["low"]
        upper_wick = c["high"] - max(c["close"], c["open"])
        return lower_wick > 2 * body and upper_wick < body * 0.5 and body > 0

    def _is_bullish_engulfing(self, df: pd.DataFrame) -> bool:
        if len(df) < 2:
            return False
        prev, curr = df.iloc[-2], df.iloc[-1]
        prev_bearish = prev["close"] < prev["open"]
        curr_bullish = curr["close"] > curr["open"]
        engulfs = curr["open"] <= prev["close"] and curr["close"] >= prev["open"]
        return prev_bearish and curr_bullish and engulfs

    def _is_bearish_engulfing(self, df: pd.DataFrame) -> bool:
        if len(df) < 2:
            return False
        prev, curr = df.iloc[-2], df.iloc[-1]
        prev_bullish = prev["close"] > prev["open"]
        curr_bearish = curr["close"] < curr["open"]
        engulfs = curr["open"] >= prev["close"] and curr["close"] <= prev["open"]
        return prev_bullish and curr_bearish and engulfs

    async def generate_signal(self, symbol: str, df: pd.DataFrame, context: dict) -> dict | None:
        if len(df) < 30:
            return None
        try:
            ti = TechnicalIndicators()
            analysis = ti.analyze(df)
            if "error" in analysis:
                return None

            current_price = float(df["close"].iloc[-1])
            rsi = analysis["rsi_value"]
            sr = SupportResistanceAnalyzer()
            levels = sr.find_levels(df)
            support = levels["support"]
            resistance = levels["resistance"]

            near_support = abs(current_price - support) / support < 0.03
            near_resistance = abs(current_price - resistance) / resistance < 0.03

            hammer = self._is_hammer(df)
            bull_engulf = self._is_bullish_engulfing(df)
            bear_engulf = self._is_bearish_engulfing(df)

            if near_support and rsi < 45 and (hammer or bull_engulf):
                stop = sr.calculate_stop_loss(df, current_price, "long", 1.5)
                target = sr.calculate_target(df, current_price, "long", 2.0)
                pattern = "hammer" if hammer else "bullish_engulfing"
                confidence = 0.65 if bull_engulf else 0.55
                return self._build_signal(
                    symbol=symbol, asset_type="stock",
                    signal_type="buy", strength=0.7, confidence=confidence,
                    entry_price=current_price, target_price=target, stop_loss=stop,
                    reasoning=f"Swing buy at support. Pattern={pattern}, RSI={rsi:.1f}, support={support:.2f}",
                    timeframe="swing_2-10d",
                )

            if near_resistance and rsi > 60 and bear_engulf:
                stop = sr.calculate_stop_loss(df, current_price, "short", 1.5)
                target = sr.calculate_target(df, current_price, "short", 2.0)
                return self._build_signal(
                    symbol=symbol, asset_type="stock",
                    signal_type="sell", strength=0.65, confidence=0.60,
                    entry_price=current_price, target_price=target, stop_loss=stop,
                    reasoning=f"Swing sell at resistance. Pattern=bearish_engulfing, RSI={rsi:.1f}, resistance={resistance:.2f}",
                    timeframe="swing_2-10d",
                )
            return None
        except Exception as e:
            logger.warning(f"SwingStrategy error for {symbol}: {e}")
            return None
