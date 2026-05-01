from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/technical/{symbol}")
async def technical_analysis(
    symbol: str,
    timeframe: str = Query("1d", regex="^(1m|5m|15m|1h|4h|1d|1w)$"),
):
    try:
        import yfinance as yf
        import pandas as pd
        from app.analysis.technical.indicators import TechnicalIndicators
        from app.analysis.technical.support_resistance import SupportResistanceAnalyzer

        interval_map = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "1h", "4h": "1h", "1d": "1d", "1w": "1wk"}
        period_map = {"1m": "7d", "5m": "60d", "15m": "60d", "1h": "730d", "4h": "730d", "1d": "2y", "1w": "5y"}

        ticker = yf.Ticker(symbol.upper())
        df = ticker.history(period=period_map.get(timeframe, "1y"), interval=interval_map.get(timeframe, "1d"))
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data for {symbol}")

        df.columns = [c.lower() for c in df.columns]
        df.index = pd.to_datetime(df.index, utc=True)

        analysis = TechnicalIndicators.analyze(df)
        sr = SupportResistanceAnalyzer()
        current_price = float(df["close"].iloc[-1])
        levels = sr.find_levels(df)

        return {
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "current_price": current_price,
            "indicators": analysis,
            "support": levels["support"],
            "resistance": levels["resistance"],
            "key_levels": levels["key_levels"],
            "stop_loss_long": sr.calculate_stop_loss(df, current_price, "long"),
            "stop_loss_short": sr.calculate_stop_loss(df, current_price, "short"),
            "target_long": sr.calculate_target(df, current_price, "long"),
            "target_short": sr.calculate_target(df, current_price, "short"),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/options/{symbol}")
async def options_analysis(symbol: str, expiration: str | None = None):
    try:
        import yfinance as yf
        from app.analysis.options.greeks import OptionsGreeksCalculator
        from app.analysis.options.iv_analysis import IVAnalyzer

        ticker = yf.Ticker(symbol.upper())
        expirations = ticker.options
        if not expirations:
            raise HTTPException(status_code=404, detail=f"No options data for {symbol}")

        exp = expiration if expiration in expirations else expirations[0]
        chain = ticker.option_chain(exp)
        current_price = ticker.fast_info.last_price

        calls = chain.calls.copy()
        puts = chain.puts.copy()
        calls["option_type"] = "call"
        puts["option_type"] = "put"

        import pandas as pd
        full_chain = pd.concat([calls, puts], ignore_index=True)

        scorer = OptionsGreeksCalculator()
        full_chain["score"] = full_chain.apply(
            lambda r: scorer.score_option({
                "delta": r.get("delta"), "implied_volatility": r.get("impliedVolatility"),
                "bid": r.get("bid"), "ask": r.get("ask"), "volume": r.get("volume"),
            }),
            axis=1,
        )

        avg_iv = float(full_chain["impliedVolatility"].mean()) if "impliedVolatility" in full_chain.columns else 0.3
        iv_analyzer = IVAnalyzer()
        iv_env = iv_analyzer.assess_options_environment(50.0, 50.0)

        top_calls = calls.nlargest(5, "score")[["strike", "bid", "ask", "impliedVolatility", "volume", "openInterest", "score"]].to_dict("records")
        top_puts = puts.nlargest(5, "score")[["strike", "bid", "ask", "impliedVolatility", "volume", "openInterest", "score"]].to_dict("records")

        return {
            "symbol": symbol.upper(),
            "current_price": current_price,
            "expiration": exp,
            "available_expirations": list(expirations[:10]),
            "iv_environment": iv_env,
            "avg_iv": round(avg_iv, 4),
            "top_calls": top_calls,
            "top_puts": top_puts,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
