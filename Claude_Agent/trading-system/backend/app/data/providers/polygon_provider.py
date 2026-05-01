import asyncio
import json
from datetime import datetime
from typing import Callable, Awaitable

import httpx
import pandas as pd
import websockets
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .base_provider import BaseDataProvider

try:
    from app.core.config import settings
except ImportError:
    # Allows the module to be imported in isolation during testing.
    class _FallbackSettings:
        POLYGON_API_KEY: str = ""
    settings = _FallbackSettings()  # type: ignore[assignment]


# Timeframe string → (multiplier, polygon_timespan)
TIMEFRAME_MAP: dict[str, tuple[int, str]] = {
    "1m":  (1, "minute"),
    "5m":  (5, "minute"),
    "15m": (15, "minute"),
    "1h":  (1, "hour"),
    "4h":  (4, "hour"),
    "1d":  (1, "day"),
    "1w":  (1, "week"),
}

POLYGON_BASE_URL = "https://api.polygon.io"
POLYGON_WS_URL   = "wss://socket.polygon.io/stocks"


class PolygonProvider(BaseDataProvider):

    def __init__(self) -> None:
        self._api_key: str = getattr(settings, "POLYGON_API_KEY", "")
        if not self._api_key:
            logger.warning("POLYGON_API_KEY is not set; Polygon requests will fail")

    @property
    def asset_type(self) -> str:
        return "stock"

    def _check_api_key(self, context: str) -> bool:
        """Return False and warn if the API key is absent."""
        if not self._api_key:
            logger.warning("Skipping Polygon {} — POLYGON_API_KEY is empty", context)
            return False
        return True

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPError),
        reraise=True,
    )
    async def get_historical_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> pd.DataFrame:
        if not self._check_api_key("historical OHLCV"):
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

        mapping = TIMEFRAME_MAP.get(timeframe)
        if mapping is None:
            raise ValueError(f"Unsupported timeframe '{timeframe}'. Supported: {list(TIMEFRAME_MAP)}")

        multiplier, timespan = mapping
        from_date = start.strftime("%Y-%m-%d")
        to_date   = end.strftime("%Y-%m-%d")

        url = (
            f"{POLYGON_BASE_URL}/v2/aggs/ticker/{symbol}/range"
            f"/{multiplier}/{timespan}/{from_date}/{to_date}"
        )
        params = {"apiKey": self._api_key, "limit": 50000, "adjusted": "true", "sort": "asc"}

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()

        results = payload.get("results") or []
        if not results:
            logger.warning("Polygon returned no results | symbol={} timeframe={} from={} to={}", symbol, timeframe, from_date, to_date)
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

        df = pd.DataFrame(results)

        # Polygon uses single-letter keys: t=timestamp(ms), o=open, h=high, l=low, c=close, v=volume
        df = df.rename(columns={"t": "timestamp", "o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"})
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)

        return self.normalize_dataframe(df)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPError),
        reraise=True,
    )
    async def get_current_price(self, symbol: str) -> float:
        if not self._check_api_key("current price"):
            return float("nan")

        url = f"{POLYGON_BASE_URL}/v2/last/trade/{symbol}"
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params={"apiKey": self._api_key})
            response.raise_for_status()
            payload = response.json()

        price = payload["results"]["p"]
        logger.debug("Polygon current price | symbol={} price={}", symbol, price)
        return float(price)

    async def get_options_chain(
        self,
        symbol: str,
        expiration: str | None = None,
    ) -> pd.DataFrame:
        raise NotImplementedError(
            "Polygon options chain is not implemented; use YFinanceProvider.get_options_chain instead"
        )

    async def subscribe_live(
        self,
        symbol: str,
        callback: Callable[[dict], Awaitable[None]],
    ) -> None:
        """Connect to Polygon WebSocket and stream trades for `symbol`.

        The connection authenticates, subscribes to T.{symbol} (trade events),
        then enters a receive loop that parses each message and calls `callback`
        with a normalised price dict.  Intended to be run as a long-lived asyncio
        task; the caller is responsible for cancellation and reconnection.
        """
        if not self._check_api_key("live subscription"):
            return

        async with websockets.connect(POLYGON_WS_URL) as ws:
            # Step 1 — authentication
            await ws.send(json.dumps({"action": "auth", "params": self._api_key}))
            auth_response = json.loads(await ws.recv())
            if not any(msg.get("status") == "auth_success" for msg in auth_response):
                raise ConnectionError(f"Polygon WebSocket authentication failed: {auth_response}")

            # Step 2 — subscribe to trade events
            await ws.send(json.dumps({"action": "subscribe", "params": f"T.{symbol}"}))
            logger.info("Subscribed to Polygon live trades | symbol={}", symbol)

            async for raw_message in ws:
                events: list[dict] = json.loads(raw_message)
                for event in events:
                    if event.get("ev") != "T":
                        continue
                    price_data = {
                        "symbol":    event.get("sym", symbol),
                        "price":     event.get("p"),
                        "volume":    event.get("s"),         # trade size
                        "timestamp": event.get("t"),         # epoch ms
                        "bid":       None,
                        "ask":       None,
                    }
                    await callback(price_data)
