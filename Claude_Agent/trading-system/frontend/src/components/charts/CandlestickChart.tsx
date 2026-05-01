'use client';

import {
  useEffect,
  useRef,
  useImperativeHandle,
  forwardRef,
  useCallback,
} from 'react';
import {
  createChart,
  type IChartApi,
  type ISeriesApi,
  type CandlestickSeriesOptions,
  type Time,
  ColorType,
  CrosshairMode,
} from 'lightweight-charts';
import type { OHLCVBar } from '@/lib/api';

export interface CandlestickChartHandle {
  addSignalMarker: (
    price: number,
    type: 'buy' | 'sell',
    time: number
  ) => void;
}

interface CandlestickChartProps {
  data: OHLCVBar[];
  height?: number;
  symbol?: string;
  showVolume?: boolean;
}

const CandlestickChart = forwardRef<
  CandlestickChartHandle,
  CandlestickChartProps
>(function CandlestickChart(
  { data, height = 400, symbol, showVolume = true },
  ref
) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);

  // Expose addSignalMarker via ref
  useImperativeHandle(ref, () => ({
    addSignalMarker(price: number, type: 'buy' | 'sell', time: number) {
      if (!candleSeriesRef.current) return;
      candleSeriesRef.current.setMarkers([
        {
          time: time as Time,
          position: type === 'buy' ? 'belowBar' : 'aboveBar',
          color: type === 'buy' ? '#00d4aa' : '#ff4757',
          shape: type === 'buy' ? 'arrowUp' : 'arrowDown',
          text: type === 'buy' ? `B ${price}` : `S ${price}`,
        },
      ]);
    },
  }));

  const initChart = useCallback(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height,
      layout: {
        background: { type: ColorType.Solid, color: '#111111' },
        textColor: '#888888',
        fontSize: 12,
        fontFamily: 'JetBrains Mono, Fira Code, monospace',
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
        scaleMargins: showVolume ? { top: 0.1, bottom: 0.25 } : { top: 0.1, bottom: 0.05 },
      },
      timeScale: {
        borderColor: '#1f1f1f',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: '#00d4aa',
      downColor: '#ff4757',
      borderUpColor: '#00d4aa',
      borderDownColor: '#ff4757',
      wickUpColor: '#00d4aa',
      wickDownColor: '#ff4757',
    } as Partial<CandlestickSeriesOptions>);

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;

    if (showVolume) {
      const volumeSeries = chart.addHistogramSeries({
        color: '#1e90ff',
        priceFormat: { type: 'volume' },
        priceScaleId: 'volume',
      });
      chart.priceScale('volume').applyOptions({
        scaleMargins: { top: 0.8, bottom: 0 },
      });
      volumeSeriesRef.current = volumeSeries;
    }

    // Responsive resize
    const observer = new ResizeObserver(() => {
      if (containerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: containerRef.current.clientWidth,
        });
      }
    });
    observer.observe(containerRef.current);

    return () => {
      observer.disconnect();
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      volumeSeriesRef.current = null;
    };
  }, [height, showVolume]);

  // Init chart on mount
  useEffect(() => {
    const cleanup = initChart();
    return cleanup;
  }, [initChart]);

  // Update data when it changes
  useEffect(() => {
    if (!candleSeriesRef.current || !data.length) return;

    const candleData = data.map((bar) => ({
      time: bar.time as Time,
      open: bar.open,
      high: bar.high,
      low: bar.low,
      close: bar.close,
    }));
    candleSeriesRef.current.setData(candleData);

    if (volumeSeriesRef.current) {
      const volumeData = data.map((bar) => ({
        time: bar.time as Time,
        value: bar.volume,
        color: bar.close >= bar.open ? '#00d4aa30' : '#ff475730',
      }));
      volumeSeriesRef.current.setData(volumeData);
    }

    chartRef.current?.timeScale().fitContent();
  }, [data]);

  return (
    <div className="relative">
      {symbol && (
        <div className="absolute top-2 left-3 z-10 text-xs font-mono text-text-secondary bg-surface/80 px-2 py-1 rounded">
          {symbol}
        </div>
      )}
      <div ref={containerRef} style={{ height }} className="w-full" />
    </div>
  );
});

export default CandlestickChart;
