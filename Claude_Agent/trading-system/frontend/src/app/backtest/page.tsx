'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  ReferenceLine,
} from 'recharts';
import { getBacktestResults, runBacktest } from '@/lib/api';
import type { BacktestResult, BacktestParams } from '@/lib/api';
import { PageHeader } from '@/components/ui/PageHeader';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import {
  formatCurrency,
  formatPercent,
  formatDate,
  formatDateTime,
  pnlColor,
  cn,
} from '@/lib/utils';
import { Play, ChevronDown, ChevronUp, BarChart2 } from 'lucide-react';

const STRATEGIES = [
  'momentum',
  'mean_reversion',
  'trend_following',
  'breakout',
  'swing',
  'macd_crossover',
  'rsi_divergence',
];

const ASSET_TYPES = ['stock', 'option', 'crypto'] as const;

interface FormState {
  symbol: string;
  start_date: string;
  end_date: string;
  strategies: string[];
  initial_capital: string;
  asset_type: typeof ASSET_TYPES[number];
}

const DEFAULT_FORM: FormState = {
  symbol: 'AAPL',
  start_date: '2023-01-01',
  end_date: '2024-01-01',
  strategies: ['momentum'],
  initial_capital: '100000',
  asset_type: 'stock',
};

export default function BacktestPage() {
  const [form, setForm] = useState<FormState>(DEFAULT_FORM);
  const [activeResult, setActiveResult] = useState<BacktestResult | null>(null);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  const { data: historicalResults = [], refetch } = useQuery({
    queryKey: ['backtest-results'],
    queryFn: getBacktestResults,
  });

  const mutation = useMutation({
    mutationFn: runBacktest,
    onSuccess: (result) => {
      setActiveResult(result);
      refetch();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const params: BacktestParams = {
      symbol: form.symbol.toUpperCase(),
      start_date: form.start_date,
      end_date: form.end_date,
      strategies: form.strategies,
      initial_capital: parseFloat(form.initial_capital) || 100000,
      asset_type: form.asset_type,
    };
    mutation.mutate(params);
  };

  const toggleStrategy = (s: string) => {
    setForm((f) => ({
      ...f,
      strategies: f.strategies.includes(s)
        ? f.strategies.filter((x) => x !== s)
        : [...f.strategies, s],
    }));
  };

  const toggleRow = (id: string) => {
    setExpandedRows((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const displayResult = activeResult;

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title="Backtesting"
        subtitle="Simulate strategies against historical data"
      />

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Form */}
          <div className="xl:col-span-1">
            <div className="bg-surface border border-border rounded-xl p-5">
              <h2 className="text-sm font-semibold text-text-primary mb-5">
                Backtest Parameters
              </h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Symbol */}
                <div>
                  <label className="block text-xs text-text-secondary mb-1.5">
                    Symbol
                  </label>
                  <input
                    type="text"
                    value={form.symbol}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, symbol: e.target.value }))
                    }
                    className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-blue-500 font-mono"
                    placeholder="AAPL, BTC-USD…"
                    required
                  />
                </div>

                {/* Asset type */}
                <div>
                  <label className="block text-xs text-text-secondary mb-1.5">
                    Asset Type
                  </label>
                  <div className="flex gap-1">
                    {ASSET_TYPES.map((t) => (
                      <button
                        key={t}
                        type="button"
                        onClick={() => setForm((f) => ({ ...f, asset_type: t }))}
                        className={cn(
                          'flex-1 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors',
                          form.asset_type === t
                            ? 'bg-green-500/15 text-green-500'
                            : 'bg-background text-text-secondary hover:text-text-primary border border-border'
                        )}
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Dates */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-text-secondary mb-1.5">
                      Start Date
                    </label>
                    <input
                      type="date"
                      value={form.start_date}
                      onChange={(e) =>
                        setForm((f) => ({ ...f, start_date: e.target.value }))
                      }
                      className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-blue-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-text-secondary mb-1.5">
                      End Date
                    </label>
                    <input
                      type="date"
                      value={form.end_date}
                      onChange={(e) =>
                        setForm((f) => ({ ...f, end_date: e.target.value }))
                      }
                      className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-blue-500"
                      required
                    />
                  </div>
                </div>

                {/* Initial capital */}
                <div>
                  <label className="block text-xs text-text-secondary mb-1.5">
                    Initial Capital ($)
                  </label>
                  <input
                    type="number"
                    value={form.initial_capital}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, initial_capital: e.target.value }))
                    }
                    min="1000"
                    step="1000"
                    className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-blue-500 font-mono"
                    required
                  />
                </div>

                {/* Strategies */}
                <div>
                  <label className="block text-xs text-text-secondary mb-1.5">
                    Strategies (select one or more)
                  </label>
                  <div className="grid grid-cols-2 gap-1.5">
                    {STRATEGIES.map((s) => (
                      <button
                        key={s}
                        type="button"
                        onClick={() => toggleStrategy(s)}
                        className={cn(
                          'py-1.5 px-2 rounded-lg text-xs text-left transition-colors capitalize',
                          form.strategies.includes(s)
                            ? 'bg-green-500/15 text-green-500 border border-green-500/20'
                            : 'bg-background text-text-secondary border border-border hover:text-text-primary'
                        )}
                      >
                        {s.replace(/_/g, ' ')}
                      </button>
                    ))}
                  </div>
                </div>

                {mutation.isError && (
                  <p className="text-xs text-red-500 bg-red-500/10 p-2 rounded">
                    Backtest failed. Check your parameters and try again.
                  </p>
                )}

                <button
                  type="submit"
                  disabled={mutation.isPending || form.strategies.length === 0}
                  className="w-full flex items-center justify-center gap-2 py-3 rounded-lg bg-green-500 text-background font-semibold text-sm hover:bg-green-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {mutation.isPending ? (
                    <>
                      <LoadingSpinner size="sm" />
                      Running…
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4" />
                      Run Backtest
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>

          {/* Results panel */}
          <div className="xl:col-span-2 space-y-4">
            {displayResult ? (
              <BacktestResultPanel result={displayResult} />
            ) : (
              <div className="bg-surface border border-border rounded-xl flex flex-col items-center justify-center py-20">
                <BarChart2 className="w-12 h-12 text-border mb-4" />
                <p className="text-text-secondary text-sm">
                  Configure parameters and run a backtest to see results
                </p>
              </div>
            )}

            {/* Historical results */}
            {historicalResults.length > 0 && (
              <div className="bg-surface border border-border rounded-xl overflow-hidden">
                <div className="px-5 py-4 border-b border-border">
                  <h2 className="text-sm font-semibold text-text-primary">
                    Historical Runs
                  </h2>
                </div>
                <div className="divide-y divide-border">
                  {historicalResults.slice(0, 10).map((r) => (
                    <div key={r.id}>
                      <button
                        className="w-full flex items-center justify-between px-5 py-3 hover:bg-border/20 transition-colors"
                        onClick={() => {
                          setActiveResult(r);
                          toggleRow(r.id);
                        }}
                      >
                        <div className="flex items-center gap-4 text-left">
                          <div>
                            <p className="text-sm font-mono font-semibold text-text-primary">
                              {r.symbol}
                            </p>
                            <p className="text-xs text-text-secondary">
                              {formatDate(r.start_date)} → {formatDate(r.end_date)}
                            </p>
                          </div>
                          <div className="hidden sm:flex items-center gap-4">
                            <div>
                              <p className="text-xs text-text-secondary">Return</p>
                              <p
                                className={cn(
                                  'text-sm font-mono font-medium',
                                  pnlColor(r.total_return)
                                )}
                              >
                                {formatPercent(r.total_return_pct)}
                              </p>
                            </div>
                            <div>
                              <p className="text-xs text-text-secondary">Sharpe</p>
                              <p className="text-sm font-mono text-text-primary">
                                {r.sharpe_ratio.toFixed(2)}
                              </p>
                            </div>
                            <div>
                              <p className="text-xs text-text-secondary">Win Rate</p>
                              <p className="text-sm font-mono text-text-primary">
                                {formatPercent(r.win_rate, 1)}
                              </p>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 text-text-secondary">
                          <span className="text-xs">
                            {formatDateTime(r.created_at)}
                          </span>
                          {expandedRows.has(r.id) ? (
                            <ChevronUp className="w-4 h-4" />
                          ) : (
                            <ChevronDown className="w-4 h-4" />
                          )}
                        </div>
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function BacktestResultPanel({ result }: { result: BacktestResult }) {
  const equityCurveData = result.equity_curve.map((pt) => ({
    date: new Date(pt.timestamp).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    }),
    value: pt.value,
  }));

  const metrics = [
    {
      label: 'Total Return',
      value: formatPercent(result.total_return_pct),
      color: pnlColor(result.total_return),
    },
    {
      label: 'Sharpe Ratio',
      value: result.sharpe_ratio.toFixed(2),
      color:
        result.sharpe_ratio >= 1
          ? 'text-green-500'
          : result.sharpe_ratio >= 0
          ? 'text-yellow-500'
          : 'text-red-500',
    },
    {
      label: 'Max Drawdown',
      value: formatPercent(result.max_drawdown_pct),
      color: 'text-red-500',
    },
    {
      label: 'Win Rate',
      value: formatPercent(result.win_rate, 1),
      color: result.win_rate >= 50 ? 'text-green-500' : 'text-red-500',
    },
    {
      label: 'Total Trades',
      value: String(result.total_trades),
      color: 'text-text-primary',
    },
    {
      label: 'Profit Factor',
      value: result.profit_factor.toFixed(2),
      color: result.profit_factor >= 1 ? 'text-green-500' : 'text-red-500',
    },
  ];

  return (
    <div className="space-y-4">
      {/* Metrics grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {metrics.map(({ label, value, color }) => (
          <div
            key={label}
            className="bg-surface border border-border rounded-xl p-4"
          >
            <p className="text-xs text-text-secondary mb-1">{label}</p>
            <p className={cn('text-xl font-mono font-semibold', color)}>
              {value}
            </p>
          </div>
        ))}
      </div>

      {/* Additional metrics row */}
      <div className="bg-surface border border-border rounded-xl p-4 flex flex-wrap gap-6">
        <div>
          <p className="text-xs text-text-secondary">Initial Capital</p>
          <p className="text-sm font-mono text-text-primary">
            {formatCurrency(result.initial_capital)}
          </p>
        </div>
        <div>
          <p className="text-xs text-text-secondary">Final Capital</p>
          <p className={cn('text-sm font-mono', pnlColor(result.total_return))}>
            {formatCurrency(result.final_capital)}
          </p>
        </div>
        <div>
          <p className="text-xs text-text-secondary">Avg Win</p>
          <p className="text-sm font-mono text-green-500">
            {formatCurrency(result.avg_win)}
          </p>
        </div>
        <div>
          <p className="text-xs text-text-secondary">Avg Loss</p>
          <p className="text-sm font-mono text-red-500">
            {formatCurrency(result.avg_loss)}
          </p>
        </div>
        <div>
          <p className="text-xs text-text-secondary">Strategies</p>
          <p className="text-sm text-text-primary capitalize">
            {result.strategies.join(', ')}
          </p>
        </div>
      </div>

      {/* Equity curve */}
      {equityCurveData.length > 1 && (
        <div className="bg-surface border border-border rounded-xl p-5">
          <h3 className="text-sm font-semibold text-text-primary mb-4">
            Equity Curve
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={equityCurveData}>
              <CartesianGrid stroke="#1f1f1f" strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tick={{ fill: '#888888', fontSize: 11 }}
                axisLine={{ stroke: '#1f1f1f' }}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: '#888888', fontSize: 11 }}
                axisLine={{ stroke: '#1f1f1f' }}
                tickLine={false}
                tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
                width={48}
              />
              <ReferenceLine
                y={result.initial_capital}
                stroke="#1f1f1f"
                strokeDasharray="4 4"
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#111111',
                  border: '1px solid #1f1f1f',
                  borderRadius: '8px',
                  color: '#f0f0f0',
                  fontSize: '12px',
                }}
                formatter={(v: number) => [formatCurrency(v), 'Portfolio Value']}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#00d4aa"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, fill: '#00d4aa' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Trades table */}
      {result.trades.length > 0 && (
        <div className="bg-surface border border-border rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-border">
            <h3 className="text-sm font-semibold text-text-primary">
              Trade History ({result.trades.length} trades)
            </h3>
          </div>
          <div className="overflow-x-auto max-h-72">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-surface border-b border-border">
                <tr>
                  {[
                    'Entry Date',
                    'Exit Date',
                    'Symbol',
                    'Side',
                    'Entry',
                    'Exit',
                    'P&L',
                    'P&L %',
                    'Strategy',
                  ].map((h) => (
                    <th
                      key={h}
                      className="px-4 py-2.5 text-left text-xs font-medium text-text-secondary whitespace-nowrap"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {result.trades.map((trade) => (
                  <tr key={trade.id} className="hover:bg-border/20 transition-colors">
                    <td className="px-4 py-2.5 text-xs text-text-secondary font-mono whitespace-nowrap">
                      {formatDate(trade.entry_date)}
                    </td>
                    <td className="px-4 py-2.5 text-xs text-text-secondary font-mono whitespace-nowrap">
                      {formatDate(trade.exit_date)}
                    </td>
                    <td className="px-4 py-2.5 font-mono font-semibold text-text-primary">
                      {trade.symbol}
                    </td>
                    <td className="px-4 py-2.5">
                      <span
                        className={cn(
                          'text-xs px-1.5 py-0.5 rounded capitalize',
                          trade.side === 'long'
                            ? 'bg-green-500/10 text-green-500'
                            : 'bg-red-500/10 text-red-500'
                        )}
                      >
                        {trade.side}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 font-mono text-text-primary text-xs">
                      {formatCurrency(trade.entry_price)}
                    </td>
                    <td className="px-4 py-2.5 font-mono text-text-primary text-xs">
                      {formatCurrency(trade.exit_price)}
                    </td>
                    <td
                      className={cn(
                        'px-4 py-2.5 font-mono text-xs font-medium',
                        pnlColor(trade.pnl)
                      )}
                    >
                      {formatCurrency(trade.pnl)}
                    </td>
                    <td
                      className={cn(
                        'px-4 py-2.5 font-mono text-xs font-medium',
                        pnlColor(trade.pnl_pct)
                      )}
                    >
                      {formatPercent(trade.pnl_pct)}
                    </td>
                    <td className="px-4 py-2.5 text-xs text-text-secondary capitalize">
                      {trade.strategy}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
