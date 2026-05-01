from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from loguru import logger
from app.analysis.technical.indicators import TechnicalIndicators


class SupportResistanceAnalyzer:

    @staticmethod
    def find_levels(df: pd.DataFrame, lookback: int = 50) -> dict:
        if len(df) < lookback:
            lookback = len(df)
        recent = df.tail(lookback)
        prices = recent["close"].values
        peaks, _ = find_peaks(prices, distance=3, prominence=prices.std() * 0.5)
        troughs, _ = find_peaks(-prices, distance=3, prominence=prices.std() * 0.5)
        resistance_levels = sorted([float(prices[i]) for i in peaks], reverse=True)[:3] if len(peaks) > 0 else []
        support_levels = sorted([float(prices[i]) for i in troughs])[:3] if len(troughs) > 0 else []
        current = float(df["close"].iloc[-1])
        resistance = next((r for r in resistance_levels if r > current), float(recent["high"].max()))
        support = next((s for s in reversed(support_levels) if s < current), float(recent["low"].min()))
        key_levels = sorted(set(resistance_levels + support_levels))
        return {"support": support, "resistance": resistance, "key_levels": key_levels}

    @staticmethod
    def get_nearest_support(df: pd.DataFrame, current_price: float) -> float | None:
        levels = SupportResistanceAnalyzer.find_levels(df)
        below = [l for l in levels["key_levels"] if l < current_price]
        return max(below) if below else levels["support"]

    @staticmethod
    def get_nearest_resistance(df: pd.DataFrame, current_price: float) -> float | None:
        levels = SupportResistanceAnalyzer.find_levels(df)
        above = [l for l in levels["key_levels"] if l > current_price]
        return min(above) if above else levels["resistance"]

    @staticmethod
    def calculate_stop_loss(df: pd.DataFrame, current_price: float, side: str, atr_multiplier: float = 2.0) -> float:
        atr = float(TechnicalIndicators.atr(df).iloc[-1])
        if side == "long":
            return round(current_price - atr * atr_multiplier, 4)
        return round(current_price + atr * atr_multiplier, 4)

    @staticmethod
    def calculate_target(df: pd.DataFrame, current_price: float, side: str, risk_reward: float = 2.0) -> float:
        levels = SupportResistanceAnalyzer.find_levels(df)
        if side == "long":
            stop = SupportResistanceAnalyzer.calculate_stop_loss(df, current_price, "long")
            risk = current_price - stop
            rr_target = current_price + risk * risk_reward
            resistance = levels["resistance"]
            return min(rr_target, resistance) if resistance > current_price else rr_target
        stop = SupportResistanceAnalyzer.calculate_stop_loss(df, current_price, "short")
        risk = stop - current_price
        rr_target = current_price - risk * risk_reward
        support = levels["support"]
        return max(rr_target, support) if support < current_price else rr_target
