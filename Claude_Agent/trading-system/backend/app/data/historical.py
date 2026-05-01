from datetime import datetime, timezone
from typing import Any

import pandas as pd
from loguru import logger
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .providers.yfinance_provider import YFinanceProvider
from .providers.polygon_provider import PolygonProvider
from .providers.crypto_provider import CryptoProvider


# Map asset_type strings to the provider that handles them.
_ASSET_TYPE_STOCK  = "stock"
_ASSET_TYPE_OPTION = "option"
_ASSET_TYPE_CRYPTO = "crypto"

# Batch size for bulk inserts; keeps single transactions bounded in memory.
_INSERT_BATCH_SIZE = 5000


class HistoricalDataService:

    def __init__(
        self,
        db_session: AsyncSession,
        yfinance_provider: YFinanceProvider,
        polygon_provider: PolygonProvider,
        crypto_provider: CryptoProvider,
    ) -> None:
        self._db         = db_session
        self._yfinance   = yfinance_provider
        self._polygon    = polygon_provider
        self._crypto     = crypto_provider

    def _resolve_provider(self, asset_type: str) -> Any:
        if asset_type in (_ASSET_TYPE_STOCK, _ASSET_TYPE_OPTION):
            return self._yfinance
        if asset_type == _ASSET_TYPE_CRYPTO:
            return self._crypto
        raise ValueError(f"Unknown asset_type '{asset_type}'")

    async def fetch_and_store(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        asset_type: str,
    ) -> int:
        """Fetch OHLCV from the appropriate provider and bulk-insert into the DB.

        Returns the number of rows inserted (duplicates are silently skipped).
        """
        provider = self._resolve_provider(asset_type)
        logger.info("Fetching historical data | symbol={} timeframe={} asset_type={}", symbol, timeframe, asset_type)

        df = await provider.get_historical_ohlcv(symbol, timeframe, start, end)
        if df.empty:
            logger.warning("No data returned from provider | symbol={} timeframe={}", symbol, timeframe)
            return 0

        total_inserted = 0

        for batch_start in range(0, len(df), _INSERT_BATCH_SIZE):
            batch = df.iloc[batch_start : batch_start + _INSERT_BATCH_SIZE]
            rows = [
                {
                    "symbol":    symbol,
                    "timeframe": timeframe,
                    "timestamp": row.timestamp.to_pydatetime(),
                    "open":      float(row.open),
                    "high":      float(row.high),
                    "low":       float(row.low),
                    "close":     float(row.close),
                    "volume":    float(row.volume),
                }
                for row in batch.itertuples(index=False)
            ]

            # ON CONFLICT DO NOTHING prevents duplicate insertion when a pipeline
            # reruns over an overlapping date range (idempotent by design).
            insert_sql = text("""
                INSERT INTO ohlcv (symbol, timeframe, timestamp, open, high, low, close, volume)
                VALUES (:symbol, :timeframe, :timestamp, :open, :high, :low, :close, :volume)
                ON CONFLICT (symbol, timeframe, timestamp) DO NOTHING
            """)

            try:
                result = await self._db.execute(insert_sql, rows)
                await self._db.commit()
                total_inserted += result.rowcount
            except IntegrityError:
                await self._db.rollback()
                logger.warning("IntegrityError on batch insert | symbol={} — falling back to row-by-row", symbol)
                for row in rows:
                    try:
                        await self._db.execute(insert_sql, row)
                        await self._db.commit()
                        total_inserted += 1
                    except IntegrityError:
                        await self._db.rollback()

        logger.info("Stored {} rows | symbol={} timeframe={}", total_inserted, symbol, timeframe)
        return total_inserted

    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> pd.DataFrame:
        """Return OHLCV data, supplementing DB gaps from the live provider.

        Query the database first; if the returned range does not cover the full
        requested window, fetch the missing tail from the provider and store it.
        """
        query = text("""
            SELECT timestamp, open, high, low, close, volume
            FROM ohlcv
            WHERE symbol    = :symbol
              AND timeframe  = :timeframe
              AND timestamp >= :start
              AND timestamp <= :end
            ORDER BY timestamp ASC
        """)

        result = await self._db.execute(query, {"symbol": symbol, "timeframe": timeframe, "start": start, "end": end})
        rows = result.fetchall()

        if rows:
            df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

            db_end = df["timestamp"].max().to_pydatetime()
            end_utc = end.replace(tzinfo=timezone.utc) if end.tzinfo is None else end

            # Only reach out to the provider if the DB is missing recent data.
            if db_end < end_utc:
                logger.debug("DB gap detected | symbol={} fetching from {} to {}", symbol, db_end, end_utc)
                asset_type = await self._infer_asset_type(symbol)
                await self.fetch_and_store(symbol, timeframe, db_end, end_utc, asset_type)

                result2 = await self._db.execute(query, {"symbol": symbol, "timeframe": timeframe, "start": start, "end": end})
                rows = result2.fetchall()
                df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
                df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

            return df.reset_index(drop=True)

        # Nothing in DB — fetch everything from the provider.
        logger.debug("No DB data found; fetching from provider | symbol={}", symbol)
        asset_type = await self._infer_asset_type(symbol)
        await self.fetch_and_store(symbol, timeframe, start, end, asset_type)

        result3 = await self._db.execute(query, {"symbol": symbol, "timeframe": timeframe, "start": start, "end": end})
        rows = result3.fetchall()
        if not rows:
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

        df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        return df.reset_index(drop=True)

    async def _infer_asset_type(self, symbol: str) -> str:
        """Best-effort asset_type inference from the ohlcv table; defaults to stock."""
        query = text("SELECT asset_type FROM ohlcv WHERE symbol = :symbol LIMIT 1")
        result = await self._db.execute(query, {"symbol": symbol})
        row = result.fetchone()
        return row[0] if row else _ASSET_TYPE_STOCK

    async def bulk_seed(self, symbols_config: list[dict]) -> None:
        """Seed historical data for multiple symbols concurrently.

        Each config entry must have: symbol, asset_type, timeframes (list[str]),
        lookback_days (int).
        """
        import asyncio
        from datetime import timedelta

        async def seed_one(cfg: dict) -> None:
            symbol      = cfg["symbol"]
            asset_type  = cfg["asset_type"]
            timeframes  = cfg.get("timeframes", ["1d"])
            lookback    = cfg.get("lookback_days", 365)
            end         = datetime.now(tz=timezone.utc)
            start       = end - timedelta(days=lookback)

            for tf in timeframes:
                try:
                    inserted = await self.fetch_and_store(symbol, tf, start, end, asset_type)
                    logger.info("Seeded | symbol={} timeframe={} rows={}", symbol, tf, inserted)
                except Exception as exc:
                    logger.error("Seed failed | symbol={} timeframe={} error={}", symbol, tf, exc)

        logger.info("Starting bulk seed for {} symbols", len(symbols_config))
        await asyncio.gather(*[seed_one(cfg) for cfg in symbols_config])
        logger.info("Bulk seed complete")

    async def get_available_symbols(self) -> list[dict]:
        query = text("""
            SELECT symbol, asset_type, COUNT(*) AS row_count,
                   MIN(timestamp) AS earliest, MAX(timestamp) AS latest
            FROM ohlcv
            GROUP BY symbol, asset_type
            ORDER BY symbol
        """)
        result = await self._db.execute(query)
        rows = result.fetchall()
        return [
            {
                "symbol":     row[0],
                "asset_type": row[1],
                "row_count":  row[2],
                "earliest":   row[3],
                "latest":     row[4],
            }
            for row in rows
        ]
