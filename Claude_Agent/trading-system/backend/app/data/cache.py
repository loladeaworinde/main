import json
from typing import Any

import pandas as pd
from loguru import logger
from redis.asyncio import Redis, from_url


class MarketDataCache:

    def __init__(self, redis_url: str) -> None:
        self._redis: Redis = from_url(redis_url, decode_responses=True)

    # ── Price ──────────────────────────────────────────────────────────────────

    async def set_price(self, symbol: str, price: float, ttl: int = 10) -> None:
        await self._redis.setex(f"price:{symbol}", ttl, str(price))

    async def get_price(self, symbol: str) -> float | None:
        value = await self._redis.get(f"price:{symbol}")
        if value is None:
            return None
        try:
            return float(value)
        except ValueError:
            logger.warning("Corrupt price value in cache | symbol={} value={}", symbol, value)
            return None

    # ── OHLCV ─────────────────────────────────────────────────────────────────

    async def set_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        df: pd.DataFrame,
        ttl: int = 300,
    ) -> None:
        # orient="split" is compact and preserves column order and dtypes precisely.
        payload = df.to_json(orient="split", date_format="iso", default_handler=str)
        await self._redis.setex(f"ohlcv:{symbol}:{timeframe}", ttl, payload)

    async def get_ohlcv(self, symbol: str, timeframe: str) -> pd.DataFrame | None:
        raw = await self._redis.get(f"ohlcv:{symbol}:{timeframe}")
        if raw is None:
            return None
        try:
            df = pd.read_json(raw, orient="split")
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
            return df
        except Exception as exc:
            logger.warning("Failed to deserialise OHLCV from cache | symbol={} timeframe={} error={}", symbol, timeframe, exc)
            return None

    # ── Sentiment ─────────────────────────────────────────────────────────────

    async def set_sentiment(
        self,
        symbol: str,
        score_dict: dict,
        ttl: int = 1800,
    ) -> None:
        await self._redis.setex(f"sentiment:{symbol}", ttl, json.dumps(score_dict))

    async def get_sentiment(self, symbol: str) -> dict | None:
        raw = await self._redis.get(f"sentiment:{symbol}")
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.warning("Corrupt sentiment value in cache | symbol={} error={}", symbol, exc)
            return None

    # ── Pub/Sub ───────────────────────────────────────────────────────────────

    async def publish_signal(self, signal_dict: dict) -> None:
        """Publish a trading signal to the shared signals channel.

        Consumers (strategy engines, risk managers) subscribe to trading:signals
        and receive JSON-serialised signal dicts.
        """
        await self._redis.publish("trading:signals", json.dumps(signal_dict, default=str))

    async def publish_price_update(self, symbol: str, price: float) -> None:
        payload = json.dumps({"symbol": symbol, "price": price})
        await self._redis.publish(f"trading:prices:{symbol}", payload)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def close(self) -> None:
        await self._redis.aclose()
