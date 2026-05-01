import asyncio
from datetime import datetime, timezone
from typing import Callable, Awaitable

from loguru import logger

from .providers.polygon_provider import PolygonProvider
from .providers.crypto_provider import CryptoProvider
from .providers.yfinance_provider import YFinanceProvider


# Seconds to wait before reconnecting after a feed drops.
_RECONNECT_DELAY = 5

PriceCallback = Callable[[dict], Awaitable[None]]

PRICE_UPDATE_KEYS = frozenset({"symbol", "price", "volume", "timestamp", "bid", "ask"})


class LiveFeedManager:

    def __init__(
        self,
        polygon_provider: PolygonProvider,
        crypto_provider: CryptoProvider,
        yfinance_provider: YFinanceProvider | None = None,
    ) -> None:
        self._polygon   = polygon_provider
        self._crypto    = crypto_provider
        self._yfinance  = yfinance_provider

        # symbol → list of registered callbacks
        self.subscribers: dict[str, list[PriceCallback]] = {}

        # symbol → running asyncio.Task
        self._tasks: dict[str, asyncio.Task] = {}

    async def subscribe(
        self,
        symbol: str,
        callback: PriceCallback,
        provider: str = "polygon",
    ) -> None:
        if symbol not in self.subscribers:
            self.subscribers[symbol] = []

        self.subscribers[symbol].append(callback)
        logger.info("Callback registered | symbol={} provider={} total_callbacks={}", symbol, provider, len(self.subscribers[symbol]))

        if symbol not in self._tasks or self._tasks[symbol].done():
            await self.start_feed(symbol, provider)

    async def unsubscribe(self, symbol: str, callback: PriceCallback) -> None:
        if symbol not in self.subscribers:
            return

        try:
            self.subscribers[symbol].remove(callback)
        except ValueError:
            logger.warning("Attempted to remove a callback that was not registered | symbol={}", symbol)
            return

        logger.info("Callback removed | symbol={} remaining={}", symbol, len(self.subscribers[symbol]))

        if not self.subscribers[symbol]:
            await self._cancel_feed(symbol)
            del self.subscribers[symbol]

    async def start_feed(self, symbol: str, provider: str) -> None:
        """Launch the long-running feed task with automatic reconnection."""
        task = asyncio.create_task(
            self._feed_loop(symbol, provider),
            name=f"feed:{provider}:{symbol}",
        )
        self._tasks[symbol] = task
        logger.info("Feed task started | symbol={} provider={}", symbol, provider)

    async def _feed_loop(self, symbol: str, provider: str) -> None:
        """Reconnect loop: if the feed drops, wait and retry indefinitely."""
        while True:
            try:
                await self._run_feed(symbol, provider)
            except asyncio.CancelledError:
                logger.info("Feed task cancelled | symbol={}", symbol)
                return
            except Exception as exc:
                logger.error(
                    "Feed error — reconnecting in {}s | symbol={} provider={} error={}",
                    _RECONNECT_DELAY, symbol, provider, exc,
                )
                # Do not reconnect if there are no remaining subscribers.
                if symbol not in self.subscribers or not self.subscribers[symbol]:
                    logger.info("No subscribers left; stopping feed | symbol={}", symbol)
                    return
                await asyncio.sleep(_RECONNECT_DELAY)

    async def _run_feed(self, symbol: str, provider: str) -> None:
        async def _callback(data: dict) -> None:
            await self.broadcast(symbol, data)

        if provider == "polygon":
            await self._polygon.subscribe_live(symbol, _callback)
        elif provider == "crypto":
            await self._crypto.subscribe_live(symbol, _callback)
        else:
            raise ValueError(f"Unknown provider '{provider}'. Supported: polygon, crypto")

    async def _cancel_feed(self, symbol: str) -> None:
        task = self._tasks.pop(symbol, None)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            logger.info("Feed task stopped | symbol={}", symbol)

    async def broadcast(self, symbol: str, data: dict) -> None:
        """Deliver a price update to every registered callback for this symbol.

        Enforces the canonical price update schema; missing keys are filled with
        None so consumers always receive a complete dict.
        """
        normalised: dict = {
            "symbol":    data.get("symbol", symbol),
            "price":     data.get("price"),
            "volume":    data.get("volume"),
            "timestamp": data.get("timestamp", int(datetime.now(tz=timezone.utc).timestamp() * 1000)),
            "bid":       data.get("bid"),
            "ask":       data.get("ask"),
        }

        callbacks = list(self.subscribers.get(symbol, []))
        results = await asyncio.gather(
            *[cb(normalised) for cb in callbacks],
            return_exceptions=True,
        )

        for cb, result in zip(callbacks, results):
            if isinstance(result, Exception):
                logger.error("Callback raised an error | symbol={} callback={} error={}", symbol, cb, result)

    def get_active_feeds(self) -> list[str]:
        return [sym for sym, task in self._tasks.items() if not task.done()]
