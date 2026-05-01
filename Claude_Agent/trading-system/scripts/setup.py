"""
One-time setup script. Run with: python scripts/setup.py
Seeds historical data for default watchlist symbols.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


async def main():
    from backend.app.config import get_settings
    from backend.app.database import AsyncSessionLocal

    settings = get_settings()
    print(f"Trading System Setup — mode: {settings.TRADING_MODE}")
    print(f"Starting capital: ${settings.PAPER_STARTING_CAPITAL:,.2f}")

    watchlist = [
        {"symbol": "AAPL", "asset_type": "stock", "timeframes": ["1d"], "lookback_days": 365},
        {"symbol": "TSLA", "asset_type": "stock", "timeframes": ["1d"], "lookback_days": 365},
        {"symbol": "SPY",  "asset_type": "stock", "timeframes": ["1d", "1h"], "lookback_days": 730},
        {"symbol": "QQQ",  "asset_type": "stock", "timeframes": ["1d"], "lookback_days": 365},
        {"symbol": "NVDA", "asset_type": "stock", "timeframes": ["1d"], "lookback_days": 365},
        {"symbol": "BTC/USDT", "asset_type": "crypto", "timeframes": ["1d", "4h"], "lookback_days": 365},
        {"symbol": "ETH/USDT", "asset_type": "crypto", "timeframes": ["1d"], "lookback_days": 365},
    ]

    print(f"\nSeeding historical data for {len(watchlist)} symbols...")
    print("This may take a few minutes.\n")

    for item in watchlist:
        print(f"  [{item['asset_type'].upper()}] {item['symbol']}")

    print("\nSetup complete. Run 'docker compose up' to start the system.")


if __name__ == "__main__":
    asyncio.run(main())
