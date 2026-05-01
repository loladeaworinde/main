from __future__ import annotations
import numpy as np
import pandas as pd
from loguru import logger


class TechnicalIndicators:

    @staticmethod
    def rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        delta = df["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
        avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
        ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        return pd.DataFrame({"macd": macd_line, "signal": signal_line, "histogram": macd_line - signal_line})

    @staticmethod
    def bollinger_bands(df: pd.DataFrame, period: int = 20, std: float = 2.0) -> pd.DataFrame:
        middle = df["close"].rolling(period).mean()
        std_dev = df["close"].rolling(period).std()
        return pd.DataFrame({"upper": middle + std * std_dev, "middle": middle, "lower": middle - std * std_dev})

    @staticmethod
    def ema(df: pd.DataFrame, period: int) -> pd.Series:
        return df["close"].ewm(span=period, adjust=False).mean()

    @staticmethod
    def sma(df: pd.DataFrame, period: int) -> pd.Series:
        return df["close"].rolling(period).mean()

    @staticmethod
    def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift()).abs()
        low_close = (df["low"] - df["close"].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.ewm(com=period - 1, min_periods=period).mean()

    @staticmethod
    def stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
        low_min = df["low"].rolling(k_period).min()
        high_max = df["high"].rolling(k_period).max()
        k = 100 * (df["close"] - low_min) / (high_max - low_min).replace(0, np.nan)
        d = k.rolling(d_period).mean()
        return pd.DataFrame({"%K": k, "%D": d})

    @staticmethod
    def volume_profile(df: pd.DataFrame) -> dict:
        if df.empty or "volume" not in df.columns:
            return {"high_volume_node": None, "low_volume_node": None, "value_area_high": None, "value_area_low": None}
        price_bins = pd.cut(df["close"], bins=20)
        vol_by_price = df.groupby(price_bins, observed=True)["volume"].sum()
        hvn = vol_by_price.idxmax()
        lvn = vol_by_price.idxmin()
        total_vol = vol_by_price.sum()
        cumvol = vol_by_price.sort_index().cumsum()
        va_low_idx = (cumvol >= total_vol * 0.15).idxmax()
        va_high_idx = (cumvol >= total_vol * 0.85).idxmax()
        return {
            "high_volume_node": float(hvn.mid) if hvn is not None else None,
            "low_volume_node": float(lvn.mid) if lvn is not None else None,
            "value_area_high": float(va_high_idx.right) if va_high_idx is not None else None,
            "value_area_low": float(va_low_idx.left) if va_low_idx is not None else None,
        }

    @classmethod
    def analyze(cls, df: pd.DataFrame) -> dict:
        if len(df) < 30:
            return {"error": "insufficient_data", "overall_score": 0.0}
        try:
            rsi_vals = cls.rsi(df)
            macd_df = cls.macd(df)
            bb_df = cls.bollinger_bands(df)
            ema20 = cls.ema(df, 20)
            ema50 = cls.ema(df, 50)
            atr_val = cls.atr(df).iloc[-1]
            current_rsi = float(rsi_vals.iloc[-1])
            current_price = float(df["close"].iloc[-1])
            avg_volume = float(df["volume"].rolling(20).mean().iloc[-1]) if "volume" in df.columns else 1.0
            current_volume = float(df["volume"].iloc[-1]) if "volume" in df.columns else 1.0

            rsi_signal = "oversold" if current_rsi < 35 else ("overbought" if current_rsi > 65 else "neutral")
            macd_bullish = float(macd_df["histogram"].iloc[-1]) > 0 and float(macd_df["histogram"].iloc[-2]) <= 0
            macd_bearish = float(macd_df["histogram"].iloc[-1]) < 0 and float(macd_df["histogram"].iloc[-2]) >= 0
            macd_signal = "bullish" if macd_bullish else ("bearish" if macd_bearish else "neutral")

            bb_upper = float(bb_df["upper"].iloc[-1])
            bb_lower = float(bb_df["lower"].iloc[-1])
            bb_position = "above" if current_price > bb_upper else ("below" if current_price < bb_lower else "inside")

            ema_trend = "uptrend" if float(ema20.iloc[-1]) > float(ema50.iloc[-1]) else "downtrend"
            price_vs_ema20 = "above" if current_price > float(ema20.iloc[-1]) else "below"
            trend = ema_trend if price_vs_ema20 == ("above" if ema_trend == "uptrend" else "below") else "sideways"

            volume_signal = "high" if current_volume > avg_volume * 1.5 else ("low" if current_volume < avg_volume * 0.5 else "normal")

            score = 0.0
            if rsi_signal == "oversold": score += 0.3
            elif rsi_signal == "overbought": score -= 0.3
            if macd_signal == "bullish": score += 0.3
            elif macd_signal == "bearish": score -= 0.3
            if bb_position == "below": score += 0.2
            elif bb_position == "above": score -= 0.2
            if trend == "uptrend": score += 0.2
            elif trend == "downtrend": score -= 0.2
            overall_score = max(-1.0, min(1.0, score))

            return {
                "rsi_value": round(current_rsi, 2),
                "rsi_signal": rsi_signal,
                "macd_signal": macd_signal,
                "bb_position": bb_position,
                "trend": trend,
                "volume_signal": volume_signal,
                "atr": round(float(atr_val), 4),
                "overall_score": round(overall_score, 3),
            }
        except Exception as e:
            logger.warning(f"Technical analysis error: {e}")
            return {"error": str(e), "overall_score": 0.0}
