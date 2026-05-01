from __future__ import annotations
from datetime import date, datetime
import pandas as pd
from loguru import logger
from app.strategies.base import BaseStrategy
from app.analysis.technical.indicators import TechnicalIndicators
from app.analysis.options.greeks import OptionsGreeksCalculator
from app.analysis.options.iv_analysis import IVAnalyzer
from app.config import get_settings


class OptionsDirectionalStrategy(BaseStrategy):
    name = "options_directional"
    asset_types = ["option"]
    timeframes = ["1d"]

    def __init__(self):
        self.weight = get_settings().STRATEGY_OPTIONS_WEIGHT

    async def generate_signal(self, symbol: str, df: pd.DataFrame, context: dict) -> dict | None:
        if len(df) < 30:
            return None
        try:
            options_chain = context.get("options_chain")
            iv_analysis = context.get("iv_analysis", {})
            sentiment = context.get("sentiment", {})

            if iv_analysis.get("iv_rank", 50) > 70:
                return None

            ti = TechnicalIndicators()
            analysis = ti.analyze(df)
            if "error" in analysis:
                return None

            current_price = float(df["close"].iloc[-1])
            tech_score = analysis["overall_score"]
            sent_score = sentiment.get("score", 0)

            if tech_score > 0.3 and sent_score > 0.1:
                direction = "call"
            elif tech_score < -0.3 and sent_score < -0.1:
                direction = "put"
            else:
                return None

            if options_chain is None or options_chain.empty:
                return None

            chain = options_chain[options_chain["option_type"] == direction].copy()
            if chain.empty:
                return None

            today = date.today()
            if "expiration" in chain.columns:
                chain["days_to_exp"] = pd.to_datetime(chain["expiration"]).apply(lambda x: (x.date() - today).days)
                chain = chain[(chain["days_to_exp"] >= 21) & (chain["days_to_exp"] <= 45)]

            if chain.empty:
                return None

            chain["score"] = chain.apply(lambda r: OptionsGreeksCalculator.score_option(r.to_dict()), axis=1)
            best = chain.nlargest(1, "score").iloc[0]

            if best["score"] < 0.3:
                return None

            mid_price = (best.get("bid", 0) + best.get("ask", 0)) / 2
            max_loss = mid_price * 100
            target_gain = mid_price * 1.5 * 100

            confidence = min(0.85, (abs(tech_score) + abs(sent_score)) / 2 + 0.3)
            return self._build_signal(
                symbol=symbol, asset_type="option",
                signal_type="buy", strength=abs(tech_score), confidence=confidence,
                entry_price=mid_price, target_price=mid_price * 1.5, stop_loss=mid_price * 0.5,
                reasoning=f"Options {direction}: tech_score={tech_score:.2f}, sentiment={sent_score:.2f}, IV regime={iv_analysis.get('regime','normal')}",
                timeframe="options",
                option_type=direction,
                strike=float(best.get("strike", 0)),
                expiration=str(best.get("expiration", "")),
                estimated_premium=round(mid_price, 2),
                max_loss=round(max_loss, 2),
                target_gain=round(target_gain, 2),
            )
        except Exception as e:
            logger.warning(f"OptionsDirectionalStrategy error for {symbol}: {e}")
            return None
