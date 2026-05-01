import asyncio
from datetime import datetime, timezone
from typing import Callable, Awaitable, Any

import pandas as pd
from loguru import logger

try:
    import ccxt.async_support as ccxt
    import ccxt.pro as ccxtpro
    _CCXTPRO_AVAILABLE = True
except ImportError:
    import ccxt.async_support as ccxt  # type: ignore[no-redef]
    _CCXTPRO_AVAILABLE = False

try:
    from app.core.config import settings
except ImportError:
    class _FallbackSettings:
        BINANCE_API_KEY: str    = ""
        BINANCE_SECRET: str     = ""
        BINANCE_TESTNET: bool   = False
    settings = _FallbackSettings()  # type: ignore[assignment]

# ccxt fetch_ohlcv returns at most 1000 candles per call; we paginate beyond that.
_MAX_CANDLES_PER_CALL = 1000


class CryptoProvider:

    def __init__(self, exchange_id: str = "binance", testnet: bool = False) -> None:
        self._exchange_id = exchange_id
        self._testnet     = testnet or bool(getattr(settings, "BINANCE_TESTNET", False))

    @property
    def asset_type(self) -> str:
        return "crypto"

    def _get_exchange(self) -> Any:
        exchange_class = getattr(ccxt, self._exchange_id, None)
        if exchange_class is None:
            raise ValueError(f"ccxt does not support exchange '{self._exchange_id}'")

        api_key = getattr(settings, "BINANCE_API_KEY", "")
        secret  = getattr(settings, "BINANCE_SECRET", "")

        exchange = exchange_class({
            "apiKey": api_key,
            "secret": secret,
            "enableRateLimit": True,
        })

        if self._testnet:
            exchange.set_sandbox_mode(True)
            logger.debug("Crypto exchange initialised in sandbox/testnet mode | exchange={}", self._exchange_id)

        return exchange

    async def get_historical_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> pd.DataFrame:
        exchange = self._get_exchange()
        try:
            since_ms = int(start.replace(tzinfo=timezone.utc).timestamp() * 1000) if start.tzinfo is None else int(start.timestamp() * 1000)
            end_ms   = int(end.replace(tzinfo=timezone.utc).timestamp() * 1000)   if end.tzinfo is None   else int(end.timestamp() * 1000)

            all_candles: list[list] = []
            fetch_since = since_ms

            while fetch_since < end_ms:
                logger.debug(
                    "Fetching OHLCV page | exchange={} symbol={} timeframe={} since={}",
                    self._exchange_id, symbol, timeframe, fetch_since,
                )
                candles = await exchange.fetch_ohlcv(
                    symbol,
                    timeframe=timeframe,
                    since=fetch_since,
                    limit=_MAX_CANDLES_PER_CALL,
                )
                if not candles:
                    break

                all_candles.extend(candles)

                last_ts = candles[-1][0]
                if last_ts >= end_ms or len(candles) < _MAX_CANDLES_PER_CALL:
                    break

                # Advance past the last returned timestamp to avoid re-fetching it.
                fetch_since = last_ts + 1

            if not all_candles:
                logger.warning("ccxt returned no candles | symbol={} timeframe={}", symbol, timeframe)
                return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

            df = pd.DataFrame(all_candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df = df[df["timestamp"] <= end_ms]
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)

            for col in ("open", "high", "low", "close", "volume"):
                df[col] = df[col].astype(float)

            return df.drop_duplicates(subset=["timestamp"]).reset_index(drop=True)

        except ccxt.NetworkError as exc:
            logger.error("Network error fetching OHLCV | symbol={} error={}", symbol, exc)
            raise
        except ccxt.ExchangeError as exc:
            logger.error("Exchange error fetching OHLCV | symbol={} error={}", symbol, exc)
            raise
        finally:
            await exchange.close()

    async def get_current_price(self, symbol: str) -> float:
        exchange = self._get_exchange()
        try:
            ticker = await exchange.fetch_ticker(symbol)
            price  = ticker["last"]
            logger.debug("Current crypto price | symbol={} price={}", symbol, price)
            return float(price)
        except ccxt.BaseError as exc:
            logger.error("Error fetching current price | symbol={} error={}", symbol, exc)
            raise
        finally:
            await exchange.close()

    async def get_futures_funding_rate(self, symbol: str) -> dict | None:
        exchange = self._get_exchange()
        try:
            if not exchange.has.get("fetchFundingRate"):
                logger.warning(
                    "Exchange does not support fetchFundingRate | exchange={}",
                    self._exchange_id,
                )
                return None
            rate = await exchange.fetch_funding_rate(symbol)
            logger.debug("Funding rate | symbol={} rate={}", symbol, rate)
            return rate
        except ccxt.BaseError as exc:
            logger.error("Error fetching funding rate | symbol={} error={}", symbol, exc)
            raise
        finally:
            await exchange.close()

    async def get_options_chain(
        self,
        symbol: str,
        expiration: str | None = None,
    ) -> pd.DataFrame:
        raise NotImplementedError(
            "Crypto options chain is not supported; use YFinanceProvider for equity options"
        )

    async def subscribe_live(
        self,
        symbol: str,
        callback: Callable[[dict], Awaitable[None]],
    ) -> None:
        """Stream live ticker updates via ccxt.pro if available, else poll every 5 seconds.

        ccxt.pro's watch_ticker uses the exchange's native WebSocket feed; the
        polling fallback exists for exchanges where ccxt.pro is not installed or
        the exchange does not expose a WS ticker endpoint.
        """
        if _CCXTPRO_AVAILABLE:
            await self._subscribe_via_ccxtpro(symbol, callback)
        else:
            await self._subscribe_via_polling(symbol, callback)

    async def _subscribe_via_ccxtpro(
        self,
        symbol: str,
        callback: Callable[[dict], Awaitable[None]],
    ) -> None:
        exchange_class = getattr(ccxtpro, self._exchange_id, None)
        if exchange_class is None:
            logger.warning("ccxt.pro does not support '{}'; falling back to polling", self._exchange_id)
            await self._subscribe_via_polling(symbol, callback)
            return

        exchange = exchange_class({"enableRateLimit": True})
        if self._testnet:
            exchange.set_sandbox_mode(True)

        try:
            logger.info("Starting ccxt.pro watch_ticker | symbol={}", symbol)
            while True:
                ticker = await exchange.watch_ticker(symbol)
                await callback({
                    "symbol":    symbol,
                    "price":     ticker.get("last"),
                    "volume":    ticker.get("baseVolume"),
                    "timestamp": ticker.get("timestamp"),
                    "bid":       ticker.get("bid"),
                    "ask":       ticker.get("ask"),
                })
        except asyncio.CancelledError:
            pass
        except ccxt.BaseError as exc:
            logger.error("ccxt.pro error in watch_ticker | symbol={} error={}", symbol, exc)
            raise
        finally:
            await exchange.close()

    async def _subscribe_via_polling(
        self,
        symbol: str,
        callback: Callable[[dict], Awaitable[None]],
    ) -> None:
        logger.info("Starting polling-based live feed (5s interval) | symbol={}", symbol)
        while True:
            try:
                exchange = self._get_exchange()
                ticker   = await exchange.fetch_ticker(symbol)
                await exchange.close()
                await callback({
                    "symbol":    symbol,
                    "price":     ticker.get("last"),
                    "volume":    ticker.get("baseVolume"),
                    "timestamp": ticker.get("timestamp"),
                    "bid":       ticker.get("bid"),
                    "ask":       ticker.get("ask"),
                })
            except ccxt.BaseError as exc:
                logger.error("Polling error | symbol={} error={}", symbol, exc)
            await asyncio.sleep(5)
