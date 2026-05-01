import asyncio
from datetime import datetime
from typing import Callable, Awaitable

import pandas as pd
import yfinance as yf
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .base_provider import BaseDataProvider


# yfinance uses specific interval strings that do not match our canonical timeframe keys.
TIMEFRAME_MAP: dict[str, str] = {
    "1m":  "1m",
    "5m":  "5m",
    "15m": "15m",
    "1h":  "1h",
    "1d":  "1d",
    "1w":  "1wk",
}

OPTIONS_COLUMNS = [
    "strike", "expiration", "option_type", "bid", "ask", "last",
    "volume", "open_interest", "implied_volatility",
    "delta", "gamma", "theta", "vega",
]

# yfinance Greek columns are only present when the exchange provides them;
# absent columns are filled with NaN so the contract is always satisfied.
YF_COLUMN_RENAMES = {
    "lastPrice":          "last",
    "openInterest":       "open_interest",
    "impliedVolatility":  "implied_volatility",
}


class YFinanceProvider(BaseDataProvider):

    @property
    def asset_type(self) -> str:
        return "stock"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def get_historical_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> pd.DataFrame:
        interval = TIMEFRAME_MAP.get(timeframe)
        if interval is None:
            raise ValueError(f"Unsupported timeframe '{timeframe}'. Supported: {list(TIMEFRAME_MAP)}")

        logger.debug("Fetching historical OHLCV | symbol={} timeframe={} start={} end={}", symbol, timeframe, start, end)

        # yfinance is synchronous; run in executor to avoid blocking the event loop.
        loop = asyncio.get_running_loop()
        df: pd.DataFrame = await loop.run_in_executor(
            None,
            lambda: yf.download(
                symbol,
                start=start,
                end=end,
                interval=interval,
                progress=False,
                auto_adjust=True,
            ),
        )

        if df.empty:
            logger.warning("yfinance returned empty DataFrame | symbol={} timeframe={}", symbol, timeframe)
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

        df = df.reset_index()

        # yfinance multi-level columns appear when auto_adjust=True for some versions.
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] if col[1] == "" else col[0] for col in df.columns]

        return self.normalize_dataframe(df)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def get_current_price(self, symbol: str) -> float:
        loop = asyncio.get_running_loop()
        price: float = await loop.run_in_executor(
            None,
            lambda: yf.Ticker(symbol).fast_info.last_price,
        )
        logger.debug("Current price | symbol={} price={}", symbol, price)
        return float(price)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def get_options_chain(
        self,
        symbol: str,
        expiration: str | None = None,
    ) -> pd.DataFrame:
        loop = asyncio.get_running_loop()
        ticker = yf.Ticker(symbol)

        if expiration is None:
            expirations: tuple[str, ...] = await loop.run_in_executor(None, lambda: ticker.options)
            if not expirations:
                logger.warning("No options expirations found | symbol={}", symbol)
                return pd.DataFrame(columns=OPTIONS_COLUMNS)
            expiration = expirations[0]
            logger.debug("No expiration supplied; using nearest | symbol={} expiration={}", symbol, expiration)

        chain = await loop.run_in_executor(None, lambda: ticker.option_chain(expiration))

        calls: pd.DataFrame = chain.calls.copy()
        calls["option_type"] = "call"
        calls["expiration"] = expiration

        puts: pd.DataFrame = chain.puts.copy()
        puts["option_type"] = "put"
        puts["expiration"] = expiration

        combined = pd.concat([calls, puts], ignore_index=True)
        combined = combined.rename(columns=YF_COLUMN_RENAMES)

        # Greeks may not be present depending on exchange/feed; ensure all columns exist.
        for col in OPTIONS_COLUMNS:
            if col not in combined.columns:
                combined[col] = float("nan")

        return combined[OPTIONS_COLUMNS].reset_index(drop=True)

    async def get_all_expirations(self, symbol: str) -> list[str]:
        loop = asyncio.get_running_loop()
        ticker = yf.Ticker(symbol)
        expirations: tuple[str, ...] = await loop.run_in_executor(None, lambda: ticker.options)
        return list(expirations)

    async def subscribe_live(
        self,
        symbol: str,
        callback: Callable[[dict], Awaitable[None]],
    ) -> None:
        raise NotImplementedError("Use Alpaca or Polygon WebSocket for live data")
