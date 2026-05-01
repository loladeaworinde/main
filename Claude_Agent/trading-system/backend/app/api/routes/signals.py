from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.signals import Signal

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("/")
async def get_signals(
    limit: int = Query(50, le=200),
    executed: bool | None = None,
    asset_type: str | None = None,
    symbol: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Signal).order_by(Signal.created_at.desc())
    if executed is not None:
        query = query.where(Signal.executed == executed)
    if asset_type:
        query = query.where(Signal.asset_type == asset_type)
    if symbol:
        query = query.where(Signal.symbol == symbol.upper())
    query = query.limit(limit)

    result = await db.execute(query)
    signals = result.scalars().all()

    return [
        {
            "id": s.id,
            "symbol": s.symbol,
            "asset_type": s.asset_type,
            "signal_type": s.signal_type,
            "strength": s.strength,
            "strategy_name": s.strategy_name,
            "timeframe": s.timeframe,
            "entry_price": s.entry_price,
            "target_price": s.target_price,
            "stop_loss": s.stop_loss,
            "confidence": s.confidence,
            "sentiment_score": s.sentiment_score,
            "technical_score": s.technical_score,
            "reasoning": s.reasoning,
            "executed": s.executed,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in signals
    ]


@router.get("/{signal_id}")
async def get_signal(signal_id: int, db: AsyncSession = Depends(get_db)):
    signal = await db.get(Signal, signal_id)
    if not signal:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Signal not found")
    return signal
