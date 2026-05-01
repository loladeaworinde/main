from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import get_settings
from app.database import Base, engine
from app.api.routes import portfolio, signals, data, backtest, settings as settings_router, analysis
from app.api.websocket import websocket_endpoint as ws_handler

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting Trading System API in '{}' mode", settings.TRADING_MODE)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified / created")
    yield
    logger.info("Shutting down Trading System API")
    await engine.dispose()


app = FastAPI(
    title="Trading System API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(portfolio.router)
app.include_router(signals.router)
app.include_router(data.router)
app.include_router(backtest.router)
app.include_router(settings_router.router)
app.include_router(analysis.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Trading System API", "docs": "/docs"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "mode": settings.TRADING_MODE,
        "version": "1.0.0",
    }


@app.websocket("/ws/{client_id}")
async def websocket_route(websocket: WebSocket, client_id: str) -> None:
    await ws_handler(websocket, client_id)
