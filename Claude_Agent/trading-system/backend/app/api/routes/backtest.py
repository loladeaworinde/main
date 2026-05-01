from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import date
from typing import Literal

from app.database import get_db
from app.models.signals import BacktestResult

router = APIRouter(prefix="/backtest", tags=["backtest"])

_active_backtests: dict[str, dict] = {}


class BacktestRequest(BaseModel):
    symbols: list[str]
    start_date: date
    end_date: date
    initial_capital: float = 100_000.0
    asset_type: Literal["stock", "crypto"] = "stock"
    timeframe: Literal["1d", "1w", "1h"] = "1d"
    strategies: list[str] = ["momentum", "swing", "long_term"]


@router.post("/run")
async def run_backtest(req: BacktestRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    import uuid
    job_id = str(uuid.uuid4())[:8]
    _active_backtests[job_id] = {"status": "running", "progress": 0}

    async def _run():
        try:
            from app.strategies.momentum import MomentumStrategy
            from app.strategies.swing import SwingStrategy
            from app.strategies.long_term import LongTermStrategy
            from app.strategies.crypto.spot import CryptoSpotStrategy
            from app.strategies.ensemble import StrategyEnsemble
            from app.backtest.engine import BacktestEngine
            from app.config import get_settings

            settings = get_settings()
            strategy_map = {
                "momentum": MomentumStrategy,
                "swing": SwingStrategy,
                "long_term": LongTermStrategy,
                "crypto_spot": CryptoSpotStrategy,
            }
            strategies = [cls() for name, cls in strategy_map.items() if name in req.strategies]
            if not strategies:
                strategies = [MomentumStrategy(), SwingStrategy()]

            ensemble = StrategyEnsemble(strategies)
            engine = BacktestEngine(ensemble, settings)

            result = await engine.run(
                symbols=[s.upper() for s in req.symbols],
                start_date=req.start_date,
                end_date=req.end_date,
                initial_capital=req.initial_capital,
                asset_type=req.asset_type,
                timeframe=req.timeframe,
            )
            result["equity_curve"] = engine.get_equity_curve()
            _active_backtests[job_id] = {"status": "completed", "result": result}
        except Exception as e:
            _active_backtests[job_id] = {"status": "failed", "error": str(e)}

    background_tasks.add_task(_run)
    return {"job_id": job_id, "status": "running", "message": "Backtest started"}


@router.get("/status/{job_id}")
async def backtest_status(job_id: str):
    job = _active_backtests.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Backtest job not found")
    return job


@router.get("/results")
async def get_backtest_results(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BacktestResult).order_by(BacktestResult.created_at.desc()).limit(limit)
    )
    results = result.scalars().all()
    return [
        {
            "id": r.id,
            "strategy_name": r.strategy_name,
            "symbol": r.symbol,
            "start_date": str(r.start_date),
            "end_date": str(r.end_date),
            "initial_capital": r.initial_capital,
            "final_capital": r.final_capital,
            "total_return": r.total_return,
            "sharpe_ratio": r.sharpe_ratio,
            "max_drawdown": r.max_drawdown,
            "win_rate": r.win_rate,
            "total_trades": r.total_trades,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in results
    ]
