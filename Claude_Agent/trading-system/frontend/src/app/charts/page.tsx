'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  createChart,
  type IChartApi,
  type ISeriesApi,
  ColorType,
  CrosshairMode,
  type Time,
} from 'lightweight-charts';
import { getOHLCV, getSentiment } from '@/lib/api';
import { SignalBadge } from '@/components/signals/SignalBadge';
import { useTradingStore } from '@/lib/store';
import { PageHeader } from '@/components/ui/PageHeader';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import {
  formatCurrency,
  sentimentLabel,
  sentimentColor,
  cn,
} from '@/lib/utils';
import { Search, TrendingUp } from 'lucide-react';

type AssetType = 'Stock' | 'Crypto' | 'Options';
type Timeframe = '1m' | '5m' | '15m' | '1h' | '4h' | '1d' | '1w';

const TIMEFRAMES: Timeframe[] = ['1m', '5m', '15m', '1h', '4h', '1d', '1w'];
const ASSET_TYPES: AssetType[] = ['Stock', 'Crypto', 'Options'];

const POPULAR_SYMBOLS: Record<AssetType, string[]> = {
  Stock: ['AAPL', 'TSLA', 'NVDA', 'SPY', 'QQQ'],
  Crypto: ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD'],
  Options: ['SPY', 'QQQ', 'AAPL', 'TSLA'],
};

function useChartContainer(height: number) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height,
      layout: {
        background: { type: ColorType.Solid, color: '#111111' },
        textColor: '#888888',
        fontSize: 11,
        fontFamily: 'JetBrains Mono, monospace',
      },
      grid: {
        vertLines: { color: '#1f1f1f' },
        horzLines: { color: '#1f1f1f' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { color: '#444', labelBackgroundColor: '#1f1f1f' },
        horzLine: { color: '#444', labelBackgroundColor: '#1f1f1f' },
      },
      rightPriceScale: { borderColor: '#1f1f1f' },
      timeScale: { borderColor: '#1f1f1f', timeVisible: true },
    });
    chartRef.current = chart;

    const observer = new ResizeObserver(() => {
      if (containerRef.current && chartRef.current) {
        chartRef.current.applyOptions({ width: containerRef.current.clientWidth });
      }
    });
    observer.observe(containerRef.current);

    return () => {
      observer.disconnect();
      chart.remove();
      chartRef.current = null;
    };
  }, [height]);

  return { containerRef, chartRef };
}

export default function ChartsPage() {
  const [symbol, setSymbol] = useState('AAPL');
  const [inputValue, setInputValue] = useState('AAPL');
  const [assetType, setAssetType] = useState<AssetType>('Stock');
  const [timeframe, setTimeframe] = useState<Timeframe>('1d');

  const signals = useTradingStore((s) => s.signals);
  const activeSignals = signals.filter((s) => s.symbol === symbol).slice(0, 5);

  // Main chart
  const mainContainer = useRef<HTMLDivElement>(null);
  const mainChart = useRef<IChartApi | null>(null);
  const candleSeries = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeries = useRef<ISeriesApi<'Histogram'> | null>(null);

  // RSI chart
  const { containerRef: rsiContainer, chartRef: rsiChart } = useChartContainer(120);
  const rsiSeries = useRef<ISeriesApi<'Line'> | null>(null);
  const rsiOverbought = useRef<ISeriesApi<'Line'> | null>(null);
  const rsiOversold = useRef<ISeriesApi<'Line'> | null>(null);

  // MACD chart
  const { containerRef: macdContainer, chartRef: macdChart } = useChartContainer(120);
  const macdSeries = useRef<ISeriesApi<'Line'> | null>(null);
  const macdSignalSeries = useRef<ISeriesApi<'Line'> | null>(null);
  const macdHistSeries = useRef<ISeriesApi<'Histogram'> | null>(null);

  // Init main chart
  useEffect(() => {
    if (!mainContainer.current) return;
    const chart = createChart(mainContainer.current, {
      width: mainContainer.current.clientWidth,
      height: 400,
      layout: {
        background: { type: ColorType.Solid, color: '#111111' },
        textColor: '#888888',
        fontSize: 11,
        fontFamily: 'JetBrains Mono, monospace',
      },
      grid: {
        vertLines: { color: '#1f1f1f' },
        horzLines: { color: '#1f1f1f' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { color: '#444', labelBackgroundColor: '#1f1f1f' },
        horzLine: { color: '#444', labelBackgroundColor: '#1f1f1f' },
      },
      rightPriceScale: {
        borderColor: '#1f1f1f',
        scaleMargins: { top: 0.1, bottom: 0.25 },
      },
      timeScale: { borderColor: '#1f1f1f', timeVisible: true },
    });
    mainChart.current = chart;

    const candle = chart.addCandlestickSeries({
      upColor: '#00d4aa',
      downColor: '#ff4757',
      borderUpColor: '#00d4aa',
      borderDownColor: '#ff4757',
      wickUpColor: '#00d4aa',
      wickDownColor: '#ff4757',
    });
    candleSeries.current = candle;

    const vol = chart.addHistogramSeries({
      color: '#1e90ff',
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
    });
    chart.priceScale('volume').applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });
    volumeSeries.current = vol;

    const observer = new ResizeObserver(() => {
      if (mainContainer.current && mainChart.current) {
        mainChart.current.applyOptions({ width: mainContainer.current.clientWidth });
      }
    });
    observer.observe(mainContainer.current);

    return () => {
      observer.disconnect();
      chart.remove();
      mainChart.current = null;
      candleSeries.current = null;
      volumeSeries.current = null;
    };
  }, []);

  // Init RSI series
  useEffect(() => {
    if (!rsiChart.current) return;
    const line = rsiChart.current.addLineSeries({ color: '#ffa502', lineWidth: 1.5 });
    const over = rsiChart.current.addLineSeries({ color: '#ff4757', lineWidth: 1, lineStyle: 2 });
    const under = rsiChart.current.addLineSeries({ color: '#00d4aa', lineWidth: 1, lineStyle: 2 });
    rsiSeries.current = line;
    rsiOverbought.current = over;
    rsiOversold.current = under;
  }, [rsiChart]);

  // Init MACD series
  useEffect(() => {
    if (!macdChart.current) return;
    const macd = macdChart.current.addLineSeries({ color: '#1e90ff', lineWidth: 1.5 });
    const sig = macdChart.current.addLineSeries({ color: '#ffa502', lineWidth: 1.5 });
    const hist = macdChart.current.addHistogramSeries({ color: '#00d4aa' });
    macdSeries.current = macd;
    macdSignalSeries.current = sig;
    macdHistSeries.current = hist;
  }, [macdChart]);

  // OHLCV data query
  const { data: ohlcvData = [], isLoading } = useQuery({
    queryKey: ['ohlcv', symbol, timeframe],
    queryFn: () => getOHLCV(symbol, timeframe),
    enabled: !!symbol,
    staleTime: 60_000,
  });

  // Sentiment query
  const { data: sentiment } = useQuery({
    queryKey: ['sentiment', symbol],
    queryFn: () => getSentiment(symbol),
    enabled: !!symbol,
    staleTime: 120_000,
  });

  // Populate charts when data arrives
  useEffect(() => {
    if (!ohlcvData.length) return;

    // Candlestick + volume
    if (candleSeries.current) {
      candleSeries.current.setData(
        ohlcvData.map((b) => ({
          time: b.time as Time,
          open: b.open,
          high: b.high,
          low: b.low,
          close: b.close,
        }))
      );
    }
    if (volumeSeries.current) {
      volumeSeries.current.setData(
        ohlcvData.map((b) => ({
          time: b.time as Time,
          value: b.volume,
          color: b.close >= b.open ? '#00d4aa30' : '#ff475730',
        }))
      );
    }
    mainChart.current?.timeScale().fitContent();

    // Compute RSI (14-period)
    const closes = ohlcvData.map((b) => b.close);
    const rsiValues = computeRSI(closes, 14);
    if (rsiSeries.current && rsiValues.length) {
      const rsiData = rsiValues.map((v, i) => ({
        time: ohlcvData[i + 14].time as Time,
        value: v,
      }));
      rsiSeries.current.setData(rsiData);
      rsiOverbought.current?.setData(rsiData.map((d) => ({ time: d.time, value: 70 })));
      rsiOversold.current?.setData(rsiData.map((d) => ({ time: d.time, value: 30 })));
      rsiChart.current?.timeScale().fitContent();
    }

    // Compute MACD (12, 26, 9)
    const { macdLine, signalLine, histogram } = computeMACD(closes, 12, 26, 9);
    if (macdSeries.current && macdLine.length) {
      const offset = ohlcvData.length - macdLine.length;
      macdSeries.current.setData(
        macdLine.map((v, i) => ({ time: ohlcvData[i + offset].time as Time, value: v }))
      );
      macdSignalSeries.current?.setData(
        signalLine.map((v, i) => ({ time: ohlcvData[i + offset + (macdLine.length - signalLine.length)].time as Time, value: v }))
      );
      macdHistSeries.current?.setData(
        histogram.map((v, i) => ({
          time: ohlcvData[i + offset + (macdLine.length - histogram.length)].time as Time,
          value: v,
          color: v >= 0 ? '#00d4aa60' : '#ff475760',
        }))
      );
      macdChart.current?.timeScale().fitContent();
    }
  }, [ohlcvData]);

  const handleSearch = useCallback(() => {
    const trimmed = inputValue.trim().toUpperCase();
    if (trimmed) setSymbol(trimmed);
  }, [inputValue]);

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title="Chart Analysis"
        subtitle={`${symbol} — ${timeframe} chart`}
      />

      <div className="flex-1 overflow-y-auto">
        {/* Controls bar */}
        <div className="px-6 py-4 border-b border-border flex flex-wrap items-center gap-4">
          {/* Symbol search */}
          <div className="flex items-center gap-2">
            <div className="relative">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Symbol (e.g. AAPL)"
                className="w-44 bg-border border border-border rounded-lg px-3 py-2 text-sm text-text-primary placeholder-text-secondary focus:outline-none focus:border-blue-500 font-mono"
                aria-label="Symbol search"
              />
            </div>
            <button
              onClick={handleSearch}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-blue-500/10 text-blue-500 border border-blue-500/20 hover:bg-blue-500/20 text-sm font-medium transition-colors"
            >
              <Search className="w-3.5 h-3.5" />
              Search
            </button>
          </div>

          {/* Asset type */}
          <div className="flex items-center gap-1">
            {ASSET_TYPES.map((t) => (
              <button
                key={t}
                onClick={() => setAssetType(t)}
                className={cn(
                  'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
                  assetType === t
                    ? 'bg-green-500/15 text-green-500'
                    : 'text-text-secondary hover:text-text-primary hover:bg-border'
                )}
              >
                {t}
              </button>
            ))}
          </div>

          {/* Timeframe */}
          <div className="flex items-center gap-1">
            {TIMEFRAMES.map((tf) => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={cn(
                  'px-2.5 py-1.5 rounded-lg text-xs font-mono font-medium transition-colors',
                  timeframe === tf
                    ? 'bg-green-500/15 text-green-500'
                    : 'text-text-secondary hover:text-text-primary hover:bg-border'
                )}
              >
                {tf}
              </button>
            ))}
          </div>

          {/* Popular symbols */}
          <div className="flex items-center gap-1 ml-auto">
            <span className="text-xs text-text-secondary mr-1">Quick:</span>
            {POPULAR_SYMBOLS[assetType].map((s) => (
              <button
                key={s}
                onClick={() => {
                  setInputValue(s);
                  setSymbol(s);
                }}
                className={cn(
                  'px-2 py-1 rounded text-xs font-mono transition-colors',
                  symbol === s
                    ? 'text-green-500 bg-green-500/10'
                    : 'text-text-secondary hover:text-text-primary hover:bg-border'
                )}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        <div className="flex">
          {/* Charts column */}
          <div className="flex-1 p-4 space-y-2 min-w-0">
            {isLoading ? (
              <div className="flex items-center justify-center h-64">
                <PageLoader />
              </div>
            ) : (
              <>
                {/* Main candlestick chart */}
                <div className="bg-surface border border-border rounded-xl overflow-hidden">
                  <div className="flex items-center justify-between px-4 py-2 border-b border-border">
                    <div className="flex items-center gap-2">
                      <TrendingUp className="w-3.5 h-3.5 text-text-secondary" />
                      <span className="text-xs font-mono font-medium text-text-primary">
                        {symbol}
                      </span>
                      <span className="text-xs text-text-secondary">{timeframe}</span>
                    </div>
                    <span className="text-xs text-text-secondary">
                      {ohlcvData.length} bars
                    </span>
                  </div>
                  <div ref={mainContainer} className="w-full" style={{ height: 400 }} />
                </div>

                {/* RSI */}
                <div className="bg-surface border border-border rounded-xl overflow-hidden">
                  <div className="px-4 py-2 border-b border-border">
                    <span className="text-xs font-mono text-text-secondary">
                      RSI (14)
                    </span>
                  </div>
                  <div ref={rsiContainer} className="w-full" style={{ height: 120 }} />
                </div>

                {/* MACD */}
                <div className="bg-surface border border-border rounded-xl overflow-hidden">
                  <div className="px-4 py-2 border-b border-border">
                    <span className="text-xs font-mono text-text-secondary">
                      MACD (12, 26, 9)
                    </span>
                  </div>
                  <div ref={macdContainer} className="w-full" style={{ height: 120 }} />
                </div>
              </>
            )}
          </div>

          {/* Right sidebar */}
          <div className="w-64 flex-shrink-0 border-l border-border p-4 space-y-4">
            {/* Sentiment */}
            {sentiment && (
              <div className="bg-surface border border-border rounded-xl p-4">
                <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">
                  Sentiment
                </h3>
                <div className="text-center mb-3">
                  <p
                    className={cn(
                      'text-2xl font-mono font-bold',
                      sentimentColor(sentiment.score)
                    )}
                  >
                    {sentiment.score.toFixed(2)}
                  </p>
                  <p className={cn('text-sm font-medium mt-1', sentimentColor(sentiment.score))}>
                    {sentimentLabel(sentiment.score)}
                  </p>
                </div>
                {/* Sentiment breakdown */}
                {(['news', 'social', 'analyst'] as const).map((src) => (
                  <div key={src} className="flex items-center justify-between mb-2">
                    <span className="text-xs text-text-secondary capitalize">{src}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1 bg-border rounded-full overflow-hidden">
                        <div
                          className={cn(
                            'h-full rounded-full',
                            sentiment.sources[src] >= 0 ? 'bg-green-500' : 'bg-red-500'
                          )}
                          style={{
                            width: `${Math.abs(sentiment.sources[src]) * 100}%`,
                          }}
                        />
                      </div>
                      <span
                        className={cn(
                          'text-xs font-mono w-8 text-right',
                          sentimentColor(sentiment.sources[src])
                        )}
                      >
                        {sentiment.sources[src].toFixed(2)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Support / Resistance */}
            {sentiment && (
              <div className="bg-surface border border-border rounded-xl p-4">
                <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">
                  Key Levels
                </h3>
                {sentiment.resistance_levels.length > 0 && (
                  <div className="mb-3">
                    <p className="text-xs text-red-500 mb-1.5 font-medium">Resistance</p>
                    {sentiment.resistance_levels.map((lvl, i) => (
                      <div
                        key={i}
                        className="flex justify-between text-xs py-1 border-b border-border last:border-0"
                      >
                        <span className="text-text-secondary">R{i + 1}</span>
                        <span className="font-mono text-red-400">
                          {formatCurrency(lvl)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
                {sentiment.support_levels.length > 0 && (
                  <div>
                    <p className="text-xs text-green-500 mb-1.5 font-medium">Support</p>
                    {sentiment.support_levels.map((lvl, i) => (
                      <div
                        key={i}
                        className="flex justify-between text-xs py-1 border-b border-border last:border-0"
                      >
                        <span className="text-text-secondary">S{i + 1}</span>
                        <span className="font-mono text-green-400">
                          {formatCurrency(lvl)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Active signals for this symbol */}
            <div className="bg-surface border border-border rounded-xl p-4">
              <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">
                Active Signals
              </h3>
              {activeSignals.length === 0 ? (
                <p className="text-xs text-text-secondary">No signals for {symbol}</p>
              ) : (
                <div className="space-y-2">
                  {activeSignals.map((sig) => (
                    <div
                      key={sig.id}
                      className="flex items-center justify-between"
                    >
                      <SignalBadge type={sig.signal_type} size="sm" />
                      <span className="text-xs text-text-secondary">
                        {sig.strategy}
                      </span>
                      <span className="text-xs font-mono text-text-secondary">
                        {sig.strength}%
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Indicator helpers ──────────────────────────────────────────────────────

function computeEMA(values: number[], period: number): number[] {
  const k = 2 / (period + 1);
  const ema: number[] = [];
  let prev = values.slice(0, period).reduce((a, b) => a + b, 0) / period;
  ema.push(prev);
  for (let i = period; i < values.length; i++) {
    prev = values[i] * k + prev * (1 - k);
    ema.push(prev);
  }
  return ema;
}

function computeRSI(closes: number[], period = 14): number[] {
  const rsi: number[] = [];
  let gains = 0;
  let losses = 0;
  for (let i = 1; i <= period; i++) {
    const diff = closes[i] - closes[i - 1];
    if (diff >= 0) gains += diff;
    else losses -= diff;
  }
  let avgGain = gains / period;
  let avgLoss = losses / period;

  for (let i = period + 1; i < closes.length; i++) {
    rsi.push(avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss));
    const diff = closes[i] - closes[i - 1];
    avgGain = (avgGain * (period - 1) + Math.max(diff, 0)) / period;
    avgLoss = (avgLoss * (period - 1) + Math.max(-diff, 0)) / period;
  }
  return rsi;
}

function computeMACD(
  closes: number[],
  fast = 12,
  slow = 26,
  signal = 9
): { macdLine: number[]; signalLine: number[]; histogram: number[] } {
  const emaFast = computeEMA(closes, fast);
  const emaSlow = computeEMA(closes, slow);
  const offset = slow - fast;
  const macdLine = emaSlow.map((v, i) => emaFast[i + offset] - v);
  const signalLine = computeEMA(macdLine, signal);
  const histOffset = macdLine.length - signalLine.length;
  const histogram = signalLine.map((v, i) => macdLine[i + histOffset] - v);
  return { macdLine, signalLine, histogram };
}
