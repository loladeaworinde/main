from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone

from app.database import get_db
from app.models.market_data import OHLCV, SentimentScore

router = APIRouter(prefix="/data", tags=["data"])

VALID_TIMEFRAMES = {"1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"}


@router.get("/ohlcv/{symbol}")
async def get_ohlcv(
    symbol: str,
    timeframe: str = Query("1d", regex="^(1m|5m|15m|30m|1h|4h|1d|1w)$"),
    limit: int = Query(200, le=500),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OHLCV)
        .where(OHLCV.symbol == symbol.upper(), OHLCV.timeframe == timeframe)
        .order_by(OHLCV.timestamp.desc())
        .limit(limit)
    )
    rows = result.scalars().all()

    if not rows:
        # Attempt live fetch via yfinance if no DB data
        try:
            import yfinance as yf
            import pandas as pd

            interval_map = {"1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m", "1h": "1h", "4h": "1h", "1d": "1d", "1w": "1wk"}
            period_map = {"1m": "7d", "5m": "60d", "15m": "60d", "30m": "60d", "1h": "730d", "4h": "730d", "1d": "5y", "1w": "10y"}
            ticker = yf.Ticker(symbol.upper())
            df = ticker.history(period=period_map.get(timeframe, "1y"), interval=interval_map.get(timeframe, "1d"))
            if df.empty:
                raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
            df.columns = [c.lower() for c in df.columns]
            df.index = pd.to_datetime(df.index, utc=True)
            df = df.tail(limit)
            return [
                {
                    "timestamp": idx.isoformat(),
                    "open": round(float(row["open"]), 4),
                    "high": round(float(row["high"]), 4),
                    "low": round(float(row["low"]), 4),
                    "close": round(float(row["close"]), 4),
                    "volume": float(row.get("volume", 0)),
                }
                for idx, row in df.iterrows()
            ]
        except ImportError:
            raise HTTPException(status_code=404, detail=f"No data for {symbol} and yfinance unavailable")

    return [
        {
            "timestamp": r.timestamp.isoformat(),
            "open": r.open,
            "high": r.high,
            "low": r.low,
            "close": r.close,
            "volume": r.volume,
        }
        for r in reversed(rows)
    ]


@router.get("/sentiment/{symbol}")
async def get_sentiment(symbol: str, db: AsyncSession = Depends(get_db)):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    result = await db.execute(
        select(SentimentScore)
        .where(SentimentScore.symbol == symbol.upper(), SentimentScore.timestamp >= cutoff)
        .order_by(SentimentScore.timestamp.desc())
        .limit(10)
    )
    scores = result.scalars().all()

    if not scores:
        return {"symbol": symbol.upper(), "score": 0.0, "confidence": 0.0, "signal": "neutral", "sources": []}

    avg_score = sum(s.score for s in scores) / len(scores)
    avg_conf = sum(s.confidence for s in scores) / len(scores)
    signal = "bullish" if avg_score > 0.3 else ("bearish" if avg_score < -0.3 else "neutral")

    return {
        "symbol": symbol.upper(),
        "score": round(avg_score, 3),
        "confidence": round(avg_conf, 3),
        "signal": signal,
        "sources": [{"source": s.source, "score": s.score, "headline": s.headline, "timestamp": s.timestamp.isoformat()} for s in scores],
    }


@router.get("/symbols")
async def get_tracked_symbols(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import distinct
    result = await db.execute(select(distinct(OHLCV.symbol), OHLCV.asset_type))
    rows = result.all()
    return [{"symbol": r[0], "asset_type": r[1]} for r in rows]
