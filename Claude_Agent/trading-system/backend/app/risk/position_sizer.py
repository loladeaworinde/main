from __future__ import annotations
from loguru import logger


class PositionSizer:

    @staticmethod
    def kelly_size(win_rate: float, avg_win: float, avg_loss: float, capital: float, kelly_fraction: float = 0.25) -> float:
        if avg_loss == 0:
            return 0.0
        b = avg_win / avg_loss
        kelly = (b * win_rate - (1 - win_rate)) / b
        return max(0.0, kelly * kelly_fraction * capital)

    @staticmethod
    def fixed_fractional_size(capital: float, risk_pct: float, entry: float, stop_loss: float) -> float:
        risk_per_share = abs(entry - stop_loss)
        if risk_per_share <= 0:
            return 0.0
        dollar_risk = capital * risk_pct
        shares = dollar_risk / risk_per_share
        return max(0.0, shares)

    @classmethod
    def size_position(cls, signal: dict, portfolio_state: dict, settings) -> dict:
        capital = portfolio_state.get("total_value", settings.PAPER_STARTING_CAPITAL)
        cash = portfolio_state.get("current_cash", capital)
        entry = signal.get("entry_price", 0)
        stop = signal.get("stop_loss", 0)
        asset_type = signal.get("asset_type", "stock")

        if entry <= 0 or stop <= 0:
            return {"shares": 0, "dollar_amount": 0, "risk_amount": 0, "pct_of_portfolio": 0}

        shares = cls.fixed_fractional_size(capital, 0.01, entry, stop)

        max_dollar = capital * settings.MAX_POSITION_SIZE
        max_shares_by_size = max_dollar / entry if entry > 0 else 0
        shares = min(shares, max_shares_by_size)

        max_shares_by_cash = cash / entry if entry > 0 else 0
        shares = min(shares, max_shares_by_cash)

        if asset_type == "option":
            contracts = max(1, int(shares / 100))
            premium = entry * 100 * contracts
            if premium < 100:
                return {"shares": 0, "dollar_amount": 0, "risk_amount": 0, "pct_of_portfolio": 0}
            return {"shares": contracts, "dollar_amount": round(premium, 2), "risk_amount": round(premium, 2), "pct_of_portfolio": round(premium / capital * 100, 2), "unit": "contracts"}

        if asset_type in ("crypto", "crypto_futures"):
            leverage = signal.get("leverage", 1)
            shares = shares * leverage
            shares = max(0.001, round(shares, 6))

        sentiment = signal.get("sentiment_override", {})
        if sentiment.get("reduce_size"):
            shares *= 0.5

        dollar_amount = shares * entry
        if dollar_amount < 100:
            return {"shares": 0, "dollar_amount": 0, "risk_amount": 0, "pct_of_portfolio": 0}

        risk_amount = abs(entry - stop) * shares
        return {
            "shares": round(shares, 4),
            "dollar_amount": round(dollar_amount, 2),
            "risk_amount": round(risk_amount, 2),
            "pct_of_portfolio": round(dollar_amount / capital * 100, 2),
        }
