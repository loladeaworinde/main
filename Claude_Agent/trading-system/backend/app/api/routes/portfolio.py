from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone, date

from app.database import get_db
from app.models.portfolio import Portfolio, Position, Order
from app.config import get_settings

router = APIRouter(prefix="/portfolio", tags=["portfolio"])
settings = get_settings()


@router.get("/summary")
async def get_portfolio_summary(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Portfolio).where(Portfolio.mode == settings.TRADING_MODE))
    portfolio = result.scalar_one_or_none()

    if not portfolio:
        portfolio = Portfolio(
            name="Main Portfolio",
            mode=settings.TRADING_MODE,
            starting_capital=settings.PAPER_STARTING_CAPITAL,
            current_cash=settings.PAPER_STARTING_CAPITAL,
        )
        db.add(portfolio)
        await db.commit()
        await db.refresh(portfolio)

    positions_result = await db.execute(
        select(Position).where(Position.portfolio_id == portfolio.id, Position.is_open == True)
    )
    positions = positions_result.scalars().all()

    positions_value = sum(
        (p.current_price or p.avg_entry_price) * p.quantity for p in positions
    )
    total_value = portfolio.current_cash + positions_value
    total_pnl = total_value - portfolio.starting_capital
    total_pnl_pct = (total_pnl / portfolio.starting_capital) * 100

    today = date.today()
    orders_today_result = await db.execute(
        select(Order).where(
            Order.portfolio_id == portfolio.id,
            func.date(Order.filled_at) == today,
            Order.status == "filled",
        )
    )

    return {
        "portfolio_id": portfolio.id,
        "mode": portfolio.mode,
        "starting_capital": portfolio.starting_capital,
        "current_cash": portfolio.current_cash,
        "positions_value": positions_value,
        "total_value": total_value,
        "total_pnl": total_pnl,
        "total_pnl_pct": round(total_pnl_pct, 2),
        "open_positions_count": len(positions),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/positions")
async def get_positions(
    asset_type: str | None = None,
    is_open: bool = True,
    db: AsyncSession = Depends(get_db),
):
    query = select(Position)
    if asset_type:
        query = query.where(Position.asset_type == asset_type)
    if is_open is not None:
        query = query.where(Position.is_open == is_open)

    result = await db.execute(query.order_by(Position.opened_at.desc()))
    positions = result.scalars().all()

    return [
        {
            "id": p.id,
            "symbol": p.symbol,
            "asset_type": p.asset_type,
            "quantity": p.quantity,
            "avg_entry_price": p.avg_entry_price,
            "current_price": p.current_price,
            "unrealized_pnl": p.unrealized_pnl,
            "realized_pnl": p.realized_pnl,
            "side": p.side,
            "strategy_source": p.strategy_source,
            "opened_at": p.opened_at.isoformat() if p.opened_at else None,
            "is_open": p.is_open,
        }
        for p in positions
    ]


@router.get("/orders")
async def get_orders(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Order).order_by(Order.created_at.desc()).limit(limit)
    )
    orders = result.scalars().all()

    return [
        {
            "id": o.id,
            "symbol": o.symbol,
            "asset_type": o.asset_type,
            "order_type": o.order_type,
            "side": o.side,
            "quantity": o.quantity,
            "status": o.status,
            "filled_price": o.filled_price,
            "broker": o.broker,
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "filled_at": o.filled_at.isoformat() if o.filled_at else None,
        }
        for o in orders
    ]
