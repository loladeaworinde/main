"""
ML + TradingView Signal Scanner
================================
Runs the trained meta-model against all watchlist symbols and displays
actionable signals. Designed to be used alongside TradingView for visual
chart confirmation.

Run inside the backend container:
    python scan_ml_signals.py
    python scan_ml_signals.py --threshold 0.50    # lower bar for more signals
    python scan_ml_signals.py --symbols AAPL,NVDA,SPY
"""
from __future__ import annotations

import argparse
import asyncio
import math
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

MODEL_DIR = Path(__file__).parent / "models"
WATCHLIST = [
    "AAPL", "TSLA", "MSFT", "NVDA", "AMZN",
    "GOOGL", "META", "SPY", "BTC-USD", "ETH-USD", "SOL-USD",
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _fetch_yf(symbol: str, start: date, end: date) -> pd.DataFrame | None:
    try:
        df = yf.download(
            symbol, start=str(start),
            end=str(end + timedelta(days=1)),
            interval="1d", auto_adjust=True,
            progress=False, multi_level_index=False,
        )
    except Exception as exc:
        return None
    if df is None or df.empty:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [c.lower() for c in df.columns]
    req = {"open", "high", "low", "close", "volume"}
    return df[list(req)].dropna() if req.issubset(set(df.columns)) else None


def _load_models():
    for fname in ["meta_model.pkl", "regime_detector.pkl", "calibration.pkl"]:
        if not (MODEL_DIR / fname).exists():
            print(f"ERROR: {MODEL_DIR / fname} not found. Run POST /tasks/train-models first.")
            sys.exit(1)

    sys.path.insert(0, str(Path(__file__).parent))
    from app.ml.meta_model import MetaModel
    from app.analysis.regime.detector import RegimeDetector
    from app.ml.calibration import CalibrationEngine

    meta   = MetaModel.load(MODEL_DIR / "meta_model.pkl")
    regime = RegimeDetector.load(MODEL_DIR / "regime_detector.pkl")
    calib  = CalibrationEngine.load(MODEL_DIR / "calibration.pkl")

    return meta, regime, calib


def _signal_for_symbol(sym: str, df: pd.DataFrame, meta, regime, calib, threshold: float) -> dict | None:
    from app.analysis.features.pipeline import FeaturePipeline
    from app.ml.meta_model import build_feature_vector

    pipe = FeaturePipeline(min_bars=50)
    try:
        fsets = pipe.compute(df, symbol=sym, mode="batch")
    except Exception as exc:
        return {"symbol": sym, "error": str(exc)}

    if not fsets:
        return {"symbol": sym, "error": "empty feature set"}

    last_fs       = fsets[-1]
    regime_result = regime.predict(last_fs.to_dict())
    fv = build_feature_vector(
        last_fs.to_dict(), regime_result,
        strategy_signals={},
        sentiment={"score": 0.0, "confidence": 0.0},
    )
    pred     = meta.predict(fv)
    raw_conf = pred["raw_confidence"]
    cal_conf = float(calib.calibrate(raw_conf)) if calib._fitted else raw_conf
    signal   = pred["signal"] if cal_conf >= threshold else "HOLD"

    # Top SHAP features
    try:
        expl = meta.explain(fv, top_n=5)
        top_features = [f"{f['feature']}={f['shap_value']:+.3f}" for f in expl.get("top_features", [])[:3]]
    except Exception:
        top_features = []

    # Price context
    close = float(df["close"].iloc[-1])
    chg1d = float((df["close"].iloc[-1] - df["close"].iloc[-2]) / df["close"].iloc[-2] * 100)
    vol20 = float(df["close"].pct_change().tail(20).std() * (252 ** 0.5) * 100)

    return {
        "symbol":          sym,
        "signal":          signal,
        "raw_signal":      pred["signal"],
        "confidence":      round(cal_conf, 4),
        "suppressed":      signal == "HOLD" and pred["signal"] != "HOLD",
        "exp_return_5d":   pred["expected_return"],
        "exp_drawdown":    pred["expected_drawdown"],
        "direction_probs": pred["direction_probs"],
        "regime":          regime_result.get("regime", "unknown"),
        "regime_conf":     round(float(regime_result.get("confidence", 0.0)), 2),
        "current_price":   close,
        "change_1d_pct":   round(chg1d, 2),
        "vol_20d_pct":     round(vol20, 2),
        "top_shap":        top_features,
    }


# ── Display ────────────────────────────────────────────────────────────────────

def _signal_icon(signal: str, suppressed: bool = False) -> str:
    if suppressed:
        return f"({signal}↓)"
    return {"BUY": "▲ BUY", "SELL": "▼ SELL", "HOLD": "— HOLD"}.get(signal, signal)


def _bar(conf: float, width: int = 20) -> str:
    filled = int(conf * width)
    return "█" * filled + "░" * (width - filled)


def display_results(results: list[dict], threshold: float) -> None:
    # Separate into actionable vs held
    actionable = [r for r in results if "error" not in r and r["signal"] != "HOLD"]
    held       = [r for r in results if "error" not in r and r["signal"] == "HOLD"]
    errors     = [r for r in results if "error" in r]

    print(f"\n{'═' * 78}")
    print(f"  ML SIGNAL SCAN  |  threshold={threshold}  |  {date.today()}")
    print(f"{'═' * 78}")

    if actionable:
        print(f"\n  ACTIONABLE SIGNALS ({len(actionable)})")
        print(f"  {'Symbol':<12} {'Signal':<12} {'Conf':>6}  {'Bar':20}  {'ExpR':>7}  {'Regime':<18}  {'1d%':>6}")
        print(f"  {'─' * 74}")
        for r in sorted(actionable, key=lambda x: -x["confidence"]):
            icon = _signal_icon(r["signal"])
            bar  = _bar(r["confidence"])
            print(
                f"  {r['symbol']:<12} {icon:<12} {r['confidence']:>6.3f}  {bar}  "
                f"{r['exp_return_5d']:>+7.3f}  {r['regime']:<18}  {r['change_1d_pct']:>+6.2f}%"
            )
            if r["top_shap"]:
                print(f"             SHAP: {', '.join(r['top_shap'])}")
            print(f"             Probs: BUY={r['direction_probs']['BUY']:.2f}  "
                  f"HOLD={r['direction_probs']['HOLD']:.2f}  SELL={r['direction_probs']['SELL']:.2f}  |  "
                  f"MaxDD={r['exp_drawdown']:+.3f}  Vol={r['vol_20d_pct']:.1f}%  ${r['current_price']:.2f}")
    else:
        print(f"\n  No actionable signals above threshold={threshold}")

    if held:
        print(f"\n  SUPPRESSED / HOLD ({len(held)}) — below confidence threshold")
        print(f"  {'Symbol':<12} {'Raw':<8} {'Conf':>6}  {'Regime':<18}  {'$Price':>10}  {'1d%':>6}")
        print(f"  {'─' * 64}")
        for r in sorted(held, key=lambda x: -x["confidence"]):
            sup_note = f" ← {r['raw_signal']}" if r.get("suppressed") else ""
            print(
                f"  {r['symbol']:<12} {'HOLD' + sup_note:<8}  {r['confidence']:>6.3f}  "
                f"{r['regime']:<18}  ${r['current_price']:>9.2f}  {r['change_1d_pct']:>+6.2f}%"
            )

    if errors:
        print(f"\n  ERRORS ({len(errors)})")
        for r in errors:
            print(f"  {r['symbol']}: {r['error']}")

    print(f"\n{'─' * 78}")

    # TradingView guidance
    if actionable:
        print("\n  TRADINGVIEW CHECKLIST  (verify these before trading)")
        print("  ─────────────────────────────────────────────────────")
        for r in actionable:
            sym = r["symbol"].replace("-", "")  # BTC-USD → BTCUSD for TV
            if r["signal"] == "BUY":
                print(f"  {r['symbol']:<10} → Look for bullish structure: "
                      f"price above EMA20, RSI recovering from 40-50, "
                      f"volume expanding on last candle")
            else:
                print(f"  {r['symbol']:<10} → Look for bearish structure: "
                      f"price below EMA20, RSI failing at 50-60, "
                      f"lower highs pattern forming")
        print()


# ── Main ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    parser = argparse.ArgumentParser(description="ML Signal Scanner")
    parser.add_argument("--symbols",   default="", help="Comma-separated symbols (default: watchlist)")
    parser.add_argument("--threshold", type=float, default=0.55, help="Confidence threshold")
    parser.add_argument("--days",      type=int,   default=400,  help="Lookback days")
    args = parser.parse_args()

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()] or WATCHLIST
    start   = date.today() - timedelta(days=args.days + 30)
    end     = date.today()

    print(f"Loading ML models from {MODEL_DIR}...")
    meta, regime, calib = _load_models()
    print(f"  Models loaded: {len(meta._feature_names)} features | "
          f"regime={'fitted' if regime._fitted else 'rule-based'} | "
          f"calib={'fitted' if calib._fitted else 'identity'}")

    print(f"\nFetching data for {len(symbols)} symbols...")
    results = []
    for sym in symbols:
        df = _fetch_yf(sym, start, end)
        if df is None or len(df) < 60:
            results.append({"symbol": sym, "error": f"insufficient data ({len(df) if df is not None else 0} bars)"})
            print(f"  {sym}: SKIP (no data)")
            continue
        print(f"  {sym}: {len(df)} bars")
        r = _signal_for_symbol(sym, df, meta, regime, calib, args.threshold)
        if r:
            results.append(r)

    display_results(results, args.threshold)


if __name__ == "__main__":
    asyncio.run(main())
