from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Literal

router = APIRouter(prefix="/analysis", tags=["analysis"])


# ── Shared helpers ────────────────────────────────────────────────────────────

import math as _math

def _sanitize(obj):
    """Recursively replace inf/nan floats with None for JSON compliance."""
    if isinstance(obj, float):
        if _math.isinf(obj) or _math.isnan(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj

def _fetch_chain(symbol: str, max_expirations: int = 3):
    """Fetch and normalise a yfinance options chain into our schema."""
    import yfinance as yf
    import pandas as pd

    ticker = yf.Ticker(symbol.upper())
    expirations = ticker.options
    if not expirations:
        raise HTTPException(status_code=404, detail=f"No options data for {symbol}")

    chains = []
    for exp in expirations[:max_expirations]:
        try:
            raw = ticker.option_chain(exp)
            for df_, otype in ((raw.calls.copy(), "call"), (raw.puts.copy(), "put")):
                df_["option_type"] = otype
                df_["expiration"]  = exp
                df_.rename(columns={
                    "impliedVolatility": "implied_volatility",
                    "openInterest":      "open_interest",
                }, inplace=True)
                chains.append(df_)
        except Exception:
            continue

    if not chains:
        raise HTTPException(status_code=404, detail=f"Could not load chain for {symbol}")

    return pd.concat(chains, ignore_index=True)


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


# ─── IV Surface ───────────────────────────────────────────────────────────────


@router.get("/iv-surface/{symbol}")
async def iv_surface_analysis(
    symbol: str,
    dte_target: int = Query(30, ge=1, le=365, description="Target DTE for skew/smile/expected-move"),
):
    """
    Full IV surface analysis: term structure, skew (25-delta risk reversal),
    volatility smile, expected move (±1σ), and IV regime (contango / backwardation).
    """
    try:
        import yfinance as yf
        from app.analysis.options.iv_surface import IVSurface

        ticker     = yf.Ticker(symbol.upper())
        spot       = ticker.fast_info.last_price
        full_chain = _fetch_chain(symbol)
        iv_surf    = IVSurface(full_chain, spot)
        analysis   = iv_surf.full_analysis(dte_target=dte_target)

        # Normalise term_structure field names to match TypeScript interface
        raw_ts = analysis.get("term_structure", [])
        term_structure = [
            {
                "expiration": p.get("expiration", ""),
                "dte":        p.get("dte", 0),
                "atm_iv":     p.get("atm_iv", 0.0),
                "call_iv":    p.get("call_iv") or p.get("iv_call", 0.0),
                "put_iv":     p.get("put_iv")  or p.get("iv_put",  0.0),
                "skew":       p.get("skew", 0.0),
            }
            for p in raw_ts
        ]
        atm_iv = term_structure[0]["atm_iv"] if term_structure else None
        skew_raw = analysis.get("skew", {})
        skew_summary = {
            "slope":      skew_raw.get("slope", 0.0) if isinstance(skew_raw, dict) else 0.0,
            "convexity":  skew_raw.get("convexity", 0.0) if isinstance(skew_raw, dict) else 0.0,
        }

        return {
            "symbol":        symbol.upper(),
            "spot":          spot,
            "atm_iv":        atm_iv,
            "term_structure": term_structure,
            "skew_summary":  skew_summary,
            "iv_regime":     analysis.get("iv_regime", {}),
            "expected_move": analysis.get("expected_move", {}),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Gamma Exposure ───────────────────────────────────────────────────────────


@router.get("/gex/{symbol}")
async def gamma_exposure(symbol: str):
    """
    Dealer gamma exposure (GEX): total GEX, regime, max-gamma strike (pinning),
    zero-gamma level (vol inflection), call wall (resistance), put wall (support).
    """
    try:
        import yfinance as yf
        from app.analysis.options.gamma_exposure import GammaExposureEngine

        ticker     = yf.Ticker(symbol.upper())
        spot       = ticker.fast_info.last_price
        full_chain = _fetch_chain(symbol)
        gex        = GammaExposureEngine(full_chain, spot)
        summary    = gex.dealer_positioning_summary()
        by_strike  = gex.gex_by_strike(n_top=20)

        key_levels = [
            {"price": float(r["strike"]), "gex": float(r["gex"]), "type": "max_gamma"}
            for _, r in by_strike.iterrows()
        ] if not by_strike.empty else []

        return {
            "symbol":      symbol.upper(),
            "spot":        spot,
            "net_gex":     summary["total_gex"],
            "regime":      summary["gex_regime"],
            "zero_gamma":  summary.get("zero_gamma_level"),
            "call_wall":   summary.get("call_wall"),
            "put_wall":    summary.get("put_wall"),
            "key_levels":  key_levels,
            "implication": summary.get("implication", ""),
            "by_expiry":   summary.get("by_expiry", []),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Options Structure Selector ───────────────────────────────────────────────


@router.get("/options-structure/{symbol}")
async def options_structure(
    symbol: str,
    directional_bias: float = Query(
        0.0, ge=-1.0, le=1.0,
        description="Directional bias: -1 (strong bear) to +1 (strong bull).",
    ),
    dte_target: int = Query(30, ge=1, le=365),
):
    """
    Recommend the optimal options structure for current market conditions.
    Pass directional_bias from your strategy signals (-1 to +1).
    """
    try:
        import yfinance as yf
        from app.analysis.options.iv_surface import IVSurface
        from app.analysis.options.gamma_exposure import GammaExposureEngine
        from app.strategies.options_structure import OptionsStructureSelector

        ticker     = yf.Ticker(symbol.upper())
        spot       = ticker.fast_info.last_price
        full_chain = _fetch_chain(symbol)

        iv_surf     = IVSurface(full_chain, spot)
        iv_analysis = iv_surf.full_analysis(dte_target=dte_target)
        gex_data    = GammaExposureEngine(full_chain, spot).key_levels()

        term   = iv_analysis.get("term_structure", [])
        atm_iv = term[0]["atm_iv"] if term else 0.30
        iv_regime_name = iv_analysis.get("iv_regime", {}).get("regime", "flat")
        if iv_regime_name == "backwardation":
            iv_rank = 75.0
        elif iv_regime_name == "contango":
            iv_rank = 35.0
        else:
            iv_rank = min(100.0, max(0.0, atm_iv * 250))

        structure = OptionsStructureSelector().select_structure(
            chain=full_chain,
            spot=spot,
            iv_rank=iv_rank,
            directional_bias=directional_bias,
            gex_data=gex_data,
            iv_analysis=iv_analysis,
            dte_target=dte_target,
        )

        import math

        def _fmt_float(v) -> str:
            if v is None:
                return "N/A"
            if math.isinf(v):
                return "Unlimited" if v > 0 else "Unlimited Loss"
            if math.isnan(v):
                return "N/A"
            return f"${v:.2f}"

        def _safe_delta(v) -> float:
            if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
                return 0.0
            return round(float(v), 2)

        if structure is None:
            raise HTTPException(status_code=404, detail="No suitable structure for current conditions.")

        bias_label = (
            "Strong Bull" if directional_bias >= 0.5 else
            "Bullish" if directional_bias > 0.1 else
            "Neutral" if abs(directional_bias) <= 0.1 else
            "Bearish" if directional_bias > -0.5 else
            "Strong Bear"
        )
        bkl = structure.breakeven_lower
        bku = structure.breakeven_upper
        if bku is not None and not math.isinf(bku) and not math.isnan(bku):
            breakeven_str = f"${bkl:.2f} – ${bku:.2f}" if bkl else f"${bku:.2f}"
        elif bkl is not None and not math.isinf(bkl) and not math.isnan(bkl):
            breakeven_str = f"${bkl:.2f}"
        else:
            breakeven_str = "N/A"

        return {
            "symbol":           symbol.upper(),
            "structure_type":   structure.structure_type.replace("_", " ").title(),
            "directional_bias": bias_label,
            "iv_rank":          round(iv_rank, 1),
            "max_profit":       _fmt_float(structure.max_profit),
            "max_loss":         _fmt_float(structure.max_loss),
            "breakeven":        breakeven_str,
            "rationale":        structure.reasoning or "",
            "legs": [
                {
                    "option_type": l.option_type,
                    "strike":      float(l.strike) if l.strike else 0.0,
                    "expiration":  str(l.expiration) if l.expiration else "",
                    "action":      l.action,
                    "contracts":   l.contracts,
                    "delta":       _safe_delta(getattr(l, "estimated_delta", None) or getattr(l, "delta", None)),
                }
                for l in structure.legs
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Portfolio Optimizer ──────────────────────────────────────────────────────


class PortfolioOptimizeRequest(BaseModel):
    symbols: list[str]
    method: Literal["mean_variance", "risk_parity", "equal_weight"] = "mean_variance"
    lookback_days: int = 252
    risk_free_rate: float = 0.05
    max_weight: float = 0.15
    expected_returns: dict[str, float] | None = None


@router.post("/portfolio/optimize")
async def optimize_portfolio(req: PortfolioOptimizeRequest):
    """
    Optimize portfolio allocation.

    Methods: mean_variance (max Sharpe), risk_parity (equal risk contribution), equal_weight.
    Returns weights, E[R], vol, Sharpe, risk contributions, correlation matrix, efficient frontier.
    """
    try:
        import asyncio
        import numpy as np
        import yfinance as yf
        import pandas as pd
        from app.risk.portfolio_optimizer import PortfolioOptimizer
        from app.risk.correlation_engine import CorrelationEngine

        symbols = [s.upper() for s in req.symbols]
        if len(symbols) < 2:
            raise HTTPException(status_code=400, detail="Provide at least 2 symbols")

        loop = asyncio.get_event_loop()
        raw  = await loop.run_in_executor(
            None,
            lambda: yf.download(
                symbols, period=f"{req.lookback_days}d", interval="1d",
                auto_adjust=True, progress=False,
            )["Close"],
        )
        if raw.empty:
            raise HTTPException(status_code=404, detail="Could not download price data")
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)

        returns   = np.log(raw / raw.shift(1)).dropna()
        available = [s for s in symbols if s in returns.columns]
        if len(available) < 2:
            raise HTTPException(status_code=400, detail="Insufficient data for requested symbols")

        corr_eng = CorrelationEngine()
        for sym in available:
            corr_eng.update(sym, raw[sym].dropna().tolist())

        high_corr = [
            (p["sym_a"], p["sym_b"], p["correlation"])
            for p in corr_eng.high_correlation_pairs(threshold=0.80, symbols=available)
        ]
        sector_map = {s: CorrelationEngine.sector(s) for s in available}

        optimizer = PortfolioOptimizer(
            returns_df=returns[available],
            expected_returns=req.expected_returns,
            risk_free_rate=req.risk_free_rate,
            max_weight=req.max_weight,
            sector_map=sector_map,
            high_corr_pairs=high_corr,
        )
        result   = optimizer.optimize(req.method)
        frontier = optimizer.efficient_frontier(n_points=20) if req.method == "mean_variance" else []
        corr_mat = corr_eng.correlation_matrix(available)

        return _sanitize({
            **result,
            "efficient_frontier": frontier,
            "correlation_matrix": corr_mat.round(4).to_dict(),
            "high_corr_pairs":    high_corr,
            "sector_map":         sector_map,
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── ML Signal Endpoint ───────────────────────────────────────────────────────

_ML_MODELS_CACHE: dict = {}


def _load_ml_models_cached():
    """Load and cache ML models on first call using their .load() class methods."""
    global _ML_MODELS_CACHE
    if _ML_MODELS_CACHE.get("loaded"):
        return _ML_MODELS_CACHE

    from pathlib import Path

    model_dir = Path(__file__).parent.parent.parent.parent / "models"
    required  = ["meta_model.pkl", "regime_detector.pkl", "calibration.pkl"]
    missing   = [r for r in required if not (model_dir / r).exists()]
    if missing:
        return {"loaded": False, "error": f"Missing model files: {missing}. Run POST /tasks/train-models first."}

    try:
        from app.ml.meta_model import MetaModel
        from app.analysis.regime.detector import RegimeDetector
        from app.ml.calibration import CalibrationEngine

        meta   = MetaModel.load(model_dir / "meta_model.pkl")
        regime = RegimeDetector.load(model_dir / "regime_detector.pkl")
        calib  = CalibrationEngine.load(model_dir / "calibration.pkl")
    except Exception as exc:
        return {"loaded": False, "error": f"Failed to load models: {exc}"}

    _ML_MODELS_CACHE = {
        "loaded":      True,
        "meta":        meta,
        "regime":      regime,
        "calibration": calib,
        "n_features":  len(meta._feature_names),
    }
    return _ML_MODELS_CACHE


@router.get("/ml-signal/{symbol}")
async def ml_signal(
    symbol: str,
    days: int = Query(400, ge=100, le=1000, description="Lookback bars for feature computation"),
    threshold: float = Query(0.55, ge=0.0, le=1.0, description="Minimum confidence to emit a signal"),
):
    """
    Generate an ML-powered trade signal for any symbol using the trained XGBoost meta-model.

    Returns the current signal (BUY/HOLD/SELL), calibrated confidence,
    expected 5-bar forward return, drawdown estimate, regime, and SHAP feature explanations.

    Requires trained models — run POST /tasks/train-models to generate them.
    """
    try:
        import asyncio
        import yfinance as yf
        import pandas as pd
        from datetime import date, timedelta
        from app.analysis.features.pipeline import FeaturePipeline
        from app.ml.meta_model import build_feature_vector

        models = await asyncio.get_event_loop().run_in_executor(None, _load_ml_models_cached)
        if not models.get("loaded"):
            raise HTTPException(status_code=503, detail=models.get("error", "Models not loaded"))

        meta   = models["meta"]
        regime = models["regime"]
        calib  = models["calibration"]

        sym   = symbol.upper()
        start = date.today() - timedelta(days=days + 30)

        def _fetch():
            df = yf.download(
                sym, start=str(start), end=str(date.today() + timedelta(days=1)),
                interval="1d", auto_adjust=True, progress=False, multi_level_index=False,
            )
            if df is None or df.empty:
                return None
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.columns = [c.lower() for c in df.columns]
            req = {"open", "high", "low", "close", "volume"}
            if not req.issubset(set(df.columns)):
                return None
            return df[list(req)].dropna()

        df = await asyncio.get_event_loop().run_in_executor(None, _fetch)
        if df is None or len(df) < 60:
            raise HTTPException(status_code=404, detail=f"Insufficient data for {sym}")

        pipe  = FeaturePipeline(min_bars=50)
        fsets = pipe.compute(df, symbol=sym, mode="batch")
        if not fsets:
            raise HTTPException(status_code=500, detail="Feature pipeline returned no data")

        last_fs       = fsets[-1]
        fs_dict       = last_fs.to_dict()
        regime_result = regime.predict(fs_dict)

        fv         = build_feature_vector(fs_dict, regime_result, strategy_signals={}, sentiment={"score": 0.0, "confidence": 0.0})
        prediction = meta.predict(fv)
        explanation = meta.explain(fv, top_n=10)

        raw_conf = prediction["raw_confidence"]
        cal_conf = float(calib.calibrate(raw_conf)) if calib._fitted else raw_conf
        signal   = prediction["signal"] if cal_conf >= threshold else "HOLD"

        current_price = float(df["close"].iloc[-1])
        change_1d     = float((df["close"].iloc[-1] - df["close"].iloc[-2]) / df["close"].iloc[-2] * 100)
        change_5d     = float((df["close"].iloc[-1] - df["close"].iloc[-6]) / df["close"].iloc[-6] * 100) if len(df) >= 6 else 0.0
        vol_20d       = float(df["close"].pct_change().tail(20).std() * (252 ** 0.5) * 100)

        return _sanitize({
            "symbol":            sym,
            "signal":            signal,
            "raw_signal":        prediction["signal"],
            "confidence":        round(cal_conf, 4),
            "raw_confidence":    raw_conf,
            "threshold":         threshold,
            "suppressed":        signal == "HOLD" and prediction["signal"] != "HOLD",
            "direction_probs":   prediction["direction_probs"],
            "expected_return":   prediction["expected_return"],
            "expected_drawdown": prediction["expected_drawdown"],
            "holding_period":    prediction["holding_period"],
            "regime": {
                "state":      regime_result.get("regime"),
                "confidence": regime_result.get("confidence"),
                "method":     regime_result.get("method"),
            },
            "shap_explanation": explanation,
            "price_context": {
                "current_price":         current_price,
                "change_1d_pct":         round(change_1d, 2),
                "change_5d_pct":         round(change_5d, 2),
                "annualized_vol_20d_pct": round(vol_20d, 2),
                "bars_analyzed":         len(fsets),
                "data_from":             str(df.index[0].date()),
                "data_to":               str(df.index[-1].date()),
            },
            "model_info": {
                "n_features":    models["n_features"],
                "regime_method": regime_result.get("method", "unknown"),
            },
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml-scan")
async def ml_scan(
    symbols: str = Query(
        "AAPL,TSLA,MSFT,NVDA,AMZN,GOOGL,META,SPY,BTC-USD,ETH-USD,SOL-USD",
        description="Comma-separated list of symbols",
    ),
    threshold: float = Query(0.55, ge=0.0, le=1.0),
    days: int = Query(400, ge=100, le=1000),
):
    """
    Scan multiple symbols through the ML model and return ranked signals.
    Only signals with confidence >= threshold are marked as BUY/SELL; others show as HOLD.
    """
    try:
        import asyncio
        import yfinance as yf
        import pandas as pd
        from datetime import date, timedelta
        from app.analysis.features.pipeline import FeaturePipeline
        from app.ml.meta_model import build_feature_vector

        models = await asyncio.get_event_loop().run_in_executor(None, _load_ml_models_cached)
        if not models.get("loaded"):
            raise HTTPException(status_code=503, detail=models.get("error", "Models not loaded"))

        meta     = models["meta"]
        regime   = models["regime"]
        calib    = models["calibration"]
        sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        start    = date.today() - timedelta(days=days + 30)
        pipe     = FeaturePipeline(min_bars=50)
        results  = []
        errors   = []

        for sym in sym_list:
            try:
                def _fetch(s=sym):
                    df = yf.download(
                        s, start=str(start), end=str(date.today() + timedelta(days=1)),
                        interval="1d", auto_adjust=True, progress=False, multi_level_index=False,
                    )
                    if df is None or df.empty:
                        return None
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    df.columns = [c.lower() for c in df.columns]
                    req = {"open", "high", "low", "close", "volume"}
                    return df[list(req)].dropna() if req.issubset(set(df.columns)) else None

                df = await asyncio.get_event_loop().run_in_executor(None, _fetch)
                if df is None or len(df) < 60:
                    errors.append({"symbol": sym, "error": "insufficient data"})
                    continue

                fsets = pipe.compute(df, symbol=sym, mode="batch")
                if not fsets:
                    errors.append({"symbol": sym, "error": "feature pipeline empty"})
                    continue

                last_fs       = fsets[-1]
                regime_result = regime.predict(last_fs.to_dict())
                fv            = build_feature_vector(
                    last_fs.to_dict(), regime_result,
                    strategy_signals={},
                    sentiment={"score": 0.0, "confidence": 0.0},
                )
                pred     = meta.predict(fv)
                raw_conf = pred["raw_confidence"]
                cal_conf = float(calib.calibrate(raw_conf)) if calib._fitted else raw_conf
                signal   = pred["signal"] if cal_conf >= threshold else "HOLD"

                results.append({
                    "symbol":            sym,
                    "signal":            signal,
                    "raw_signal":        pred["signal"],
                    "confidence":        round(cal_conf, 4),
                    "expected_return":   pred["expected_return"],
                    "expected_drawdown": pred["expected_drawdown"],
                    "regime":            regime_result.get("regime"),
                    "current_price":     round(float(df["close"].iloc[-1]), 4),
                    "change_1d_pct":     round(float((df["close"].iloc[-1] - df["close"].iloc[-2]) / df["close"].iloc[-2] * 100), 2),
                    "direction_probs":   pred["direction_probs"],
                })
            except Exception as exc:
                errors.append({"symbol": sym, "error": str(exc)})

        signal_order = {"BUY": 0, "SELL": 1, "HOLD": 2}
        results.sort(key=lambda r: (signal_order.get(r["signal"], 3), -r["confidence"]))

        return _sanitize({
            "scan_count":    len(sym_list),
            "signals_found": sum(1 for r in results if r["signal"] != "HOLD"),
            "threshold":     threshold,
            "results":       results,
            "errors":        errors,
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
