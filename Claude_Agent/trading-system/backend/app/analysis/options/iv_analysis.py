from __future__ import annotations


class IVAnalyzer:

    @staticmethod
    def iv_rank(current_iv: float, historical_ivs: list[float]) -> float:
        if not historical_ivs:
            return 50.0
        iv_min = min(historical_ivs)
        iv_max = max(historical_ivs)
        if iv_max == iv_min:
            return 50.0
        return round((current_iv - iv_min) / (iv_max - iv_min) * 100, 1)

    @staticmethod
    def iv_percentile(current_iv: float, historical_ivs: list[float]) -> float:
        if not historical_ivs:
            return 50.0
        below = sum(1 for iv in historical_ivs if iv < current_iv)
        return round(below / len(historical_ivs) * 100, 1)

    @staticmethod
    def assess_options_environment(iv_rank_val: float, iv_pct_val: float) -> dict:
        if iv_rank_val > 60:
            regime = "high_iv"
            recommendation = "Elevated IV — options are expensive. Favor selling premium or buying spreads to reduce cost basis."
            bias = "sell"
        elif iv_rank_val < 30:
            regime = "low_iv"
            recommendation = "Low IV — options are cheap. Good environment for buying calls or puts outright."
            bias = "buy"
        else:
            regime = "normal"
            recommendation = "Normal IV environment. Standard directional plays are appropriate."
            bias = "neutral"
        return {"regime": regime, "recommendation": recommendation, "bias": bias, "iv_rank": iv_rank_val, "iv_percentile": iv_pct_val}
