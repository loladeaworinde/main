from __future__ import annotations
import asyncio
import pandas as pd
from loguru import logger
from app.strategies.base import BaseStrategy


class StrategyEnsemble:

    def __init__(self, strategies: list[BaseStrategy]):
        self.strategies = strategies

    async def generate_consensus_signal(self, symbol: str, df: pd.DataFrame, context: dict) -> dict | None:
        asset_type = context.get("asset_type", "stock")
        applicable = [s for s in self.strategies if asset_type in s.asset_types]
        if not applicable:
            return None

        results = await asyncio.gather(*[s.generate_signal(symbol, df, context) for s in applicable], return_exceptions=True)

        signals = []
        for strategy, result in zip(applicable, results):
            if isinstance(result, Exception):
                logger.warning(f"Strategy {strategy.name} error: {result}")
                continue
            if result is not None:
                signals.append((strategy, result))

        if not signals:
            return None

        buy_weight = sum(s.weight * sig["confidence"] for s, sig in signals if sig["signal_type"] == "buy")
        sell_weight = sum(s.weight * sig["confidence"] for s, sig in signals if sig["signal_type"] == "sell")
        total_weight = sum(s.weight for s, _ in signals)
        if total_weight == 0:
            return None

        buy_normalized = buy_weight / total_weight
        sell_normalized = sell_weight / total_weight

        if buy_normalized > 0.6:
            consensus_type = "buy"
            matching = [(s, sig) for s, sig in signals if sig["signal_type"] == "buy"]
        elif sell_normalized > 0.6:
            consensus_type = "sell"
            matching = [(s, sig) for s, sig in signals if sig["signal_type"] == "sell"]
        else:
            return None

        if not matching:
            return None

        total_w = sum(s.weight for s, _ in matching)
        avg_strength = sum(s.weight * sig["strength"] for s, sig in matching) / total_w
        avg_confidence = sum(s.weight * sig["confidence"] for s, sig in matching) / total_w
        avg_entry = sum(s.weight * sig["entry_price"] for s, sig in matching) / total_w
        avg_target = sum(s.weight * sig["target_price"] for s, sig in matching) / total_w
        avg_stop = sum(s.weight * sig["stop_loss"] for s, sig in matching) / total_w
        participating = [s.name for s, _ in matching]
        reasoning = " | ".join(sig["reasoning"] for _, sig in matching)

        return {
            "symbol": symbol,
            "asset_type": asset_type,
            "signal_type": consensus_type,
            "strength": round(avg_strength, 3),
            "confidence": round(avg_confidence, 3),
            "entry_price": round(avg_entry, 4),
            "target_price": round(avg_target, 4),
            "stop_loss": round(avg_stop, 4),
            "participating_strategies": participating,
            "reasoning": reasoning,
            "strategy_name": "ensemble",
            "timeframe": matching[0][1].get("timeframe", "1d"),
        }

    def _normalize_weights(self, signals: list[tuple]) -> list[tuple]:
        total = sum(s.weight for s, _ in signals)
        if total == 0:
            return signals
        return [(s, sig) for s, sig in signals]
