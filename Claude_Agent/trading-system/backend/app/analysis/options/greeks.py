from __future__ import annotations
import math
from scipy.stats import norm
from loguru import logger


class OptionsGreeksCalculator:

    @staticmethod
    def _d1(S: float, K: float, T: float, r: float, sigma: float) -> float:
        return (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))

    @staticmethod
    def _d2(S: float, K: float, T: float, r: float, sigma: float) -> float:
        return OptionsGreeksCalculator._d1(S, K, T, r, sigma) - sigma * math.sqrt(T)

    @classmethod
    def bs_price(cls, S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
        if T <= 0 or sigma <= 0:
            return max(0.0, (S - K) if option_type == "call" else (K - S))
        d1 = cls._d1(S, K, T, r, sigma)
        d2 = cls._d2(S, K, T, r, sigma)
        if option_type == "call":
            return S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
        return K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

    @classmethod
    def calculate_greeks(cls, S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> dict:
        if T <= 0 or sigma <= 0:
            return {"delta": 0.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0, "rho": 0.0}
        try:
            d1 = cls._d1(S, K, T, r, sigma)
            d2 = cls._d2(S, K, T, r, sigma)
            pdf_d1 = norm.pdf(d1)
            sqrt_T = math.sqrt(T)

            gamma = pdf_d1 / (S * sigma * sqrt_T)
            vega = S * pdf_d1 * sqrt_T / 100

            if option_type == "call":
                delta = norm.cdf(d1)
                theta = (-(S * pdf_d1 * sigma) / (2 * sqrt_T) - r * K * math.exp(-r * T) * norm.cdf(d2)) / 365
                rho = K * T * math.exp(-r * T) * norm.cdf(d2) / 100
            else:
                delta = norm.cdf(d1) - 1
                theta = (-(S * pdf_d1 * sigma) / (2 * sqrt_T) + r * K * math.exp(-r * T) * norm.cdf(-d2)) / 365
                rho = -K * T * math.exp(-r * T) * norm.cdf(-d2) / 100

            return {"delta": round(delta, 4), "gamma": round(gamma, 6), "theta": round(theta, 4), "vega": round(vega, 4), "rho": round(rho, 4)}
        except Exception as e:
            logger.warning(f"Greeks calculation error: {e}")
            return {"delta": 0.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0, "rho": 0.0}

    @staticmethod
    def score_option(row: dict) -> float:
        score = 0.0
        delta = abs(row.get("delta", 0) or 0)
        if 0.3 <= delta <= 0.7:
            score += 0.35
        elif 0.2 <= delta < 0.3 or 0.7 < delta <= 0.8:
            score += 0.15

        iv = row.get("implied_volatility", 1.0) or 1.0
        if iv < 0.4:
            score += 0.25
        elif iv < 0.6:
            score += 0.15
        elif iv > 0.8:
            score -= 0.1

        bid = row.get("bid", 0) or 0
        ask = row.get("ask", 0) or 0
        if ask > 0 and bid > 0:
            mid = (bid + ask) / 2
            spread_pct = (ask - bid) / mid
            if spread_pct < 0.05:
                score += 0.2
            elif spread_pct < 0.10:
                score += 0.1
            elif spread_pct > 0.20:
                score -= 0.15

        volume = row.get("volume", 0) or 0
        if volume > 500:
            score += 0.2
        elif volume > 100:
            score += 0.1
        elif volume < 10:
            score -= 0.2

        return max(0.0, min(1.0, score))
