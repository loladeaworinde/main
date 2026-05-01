from abc import ABC, abstractmethod
from datetime import datetime
from typing import Callable, Awaitable

import pandas as pd


REQUIRED_OHLCV_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]


class BaseDataProvider(ABC):

    @property
    @abstractmethod
    def asset_type(self) -> str: ...

    @abstractmethod
    async def get_historical_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> pd.DataFrame: ...

    @abstractmethod
    async def get_current_price(self, symbol: str) -> float: ...

    @abstractmethod
    async def get_options_chain(
        self,
        symbol: str,
        expiration: str | None = None,
    ) -> pd.DataFrame: ...

    @abstractmethod
    async def subscribe_live(
        self,
        symbol: str,
        callback: Callable[[dict], Awaitable[None]],
    ) -> None: ...

    def normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Renames and reorders columns to the canonical OHLCV schema.

        Provider column names vary widely; this enforces a single contract so
        all downstream consumers can rely on identical column names and types.
        """
        column_aliases: dict[str, list[str]] = {
            "timestamp": ["datetime", "date", "time", "Datetime", "Date", "Time", "index"],
            "open": ["Open", "o"],
            "high": ["High", "h"],
            "low": ["Low", "l"],
            "close": ["Close", "c"],
            "volume": ["Volume", "v"],
        }

        rename_map: dict[str, str] = {}
        for canonical, aliases in column_aliases.items():
            if canonical in df.columns:
                continue
            for alias in aliases:
                if alias in df.columns:
                    rename_map[alias] = canonical
                    break

        df = df.rename(columns=rename_map)

        # If timestamp is the index rather than a column, promote it.
        if "timestamp" not in df.columns and df.index.name in (
            "datetime", "date", "time", "Datetime", "Date", "Time", "timestamp"
        ):
            df = df.reset_index().rename(columns={df.index.name: "timestamp"})

        missing = [c for c in REQUIRED_OHLCV_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"DataFrame is missing required columns after normalization: {missing}")

        df = df[REQUIRED_OHLCV_COLUMNS + [c for c in df.columns if c not in REQUIRED_OHLCV_COLUMNS]]

        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

        for col in ("open", "high", "low", "close"):
            df[col] = df[col].astype(float)
        df["volume"] = df["volume"].astype(float)

        return df.reset_index(drop=True)
