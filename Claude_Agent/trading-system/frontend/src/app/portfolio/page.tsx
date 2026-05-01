'use client';

import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import { getPortfolio, getPositions } from '@/lib/api';
import type { Position } from '@/lib/api';
import { useTradingStore } from '@/lib/store';
import { PageHeader } from '@/components/ui/PageHeader';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import {
  formatCurrency,
  formatPercent,
  formatDate,
  pnlColor,
  cn,
} from '@/lib/utils';
import { ArrowUpDown, X } from 'lucide-react';

type AssetFilter = 'all' | 'stock' | 'option' | 'crypto';
type SortKey = 'pnl' | 'symbol' | 'entry_date' | 'pnl_pct';
type SortDir = 'asc' | 'desc';

const FILTER_TABS: { key: AssetFilter; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'stock', label: 'Stocks' },
  { key: 'option', label: 'Options' },
  { key: 'crypto', label: 'Crypto' },
];

export default function PortfolioPage() {
  const [filter, setFilter] = useState<AssetFilter>('all');
  const [sortKey, setSortKey] = useState<SortKey>('pnl');
  const [sortDir, setSortDir] = useState<SortDir>('desc');
  const setPositions = useTradingStore((s) => s.setPositions);
  const setPortfolio = useTradingStore((s) => s.setPortfolio);

  const { data: portfolioData, isLoading: portfolioLoading } = useQuery({
    queryKey: ['portfolio'],
    queryFn: getPortfolio,
    refetchInterval: 60_000,
    onSuccess: (data) => {
      setPortfolio({
        value: data.total_value,
        cash: data.cash,
        dayPnl: data.day_pnl,
        dayPnlPct: data.day_pnl_pct,
        totalPnl: data.total_pnl,
        equityHistory: data.equity_history,
      });
    },
  });

  const { data: positions = [], isLoading: positionsLoading } = useQuery({
    queryKey: ['positions'],
    queryFn: getPositions,
    refetchInterval: 30_000,
    onSuccess: (data) => setPositions(data),
  });

  // Filtered + sorted positions
  const displayPositions = useMemo(() => {
    let list = filter === 'all'
      ? positions
      : positions.filter((p) => p.asset_type === filter);

    list = [...list].sort((a, b) => {
      let va: number | string = 0;
      let vb: number | string = 0;
      if (sortKey === 'pnl') { va = a.unrealized_pnl; vb = b.unrealized_pnl; }
      else if (sortKey === 'pnl_pct') { va = a.unrealized_pnl_pct; vb = b.unrealized_pnl_pct; }
      else if (sortKey === 'symbol') { va = a.symbol; vb = b.symbol; }
      else if (sortKey === 'entry_date') { va = a.opened_at; vb = b.opened_at; }
      if (typeof va === 'string') {
        return sortDir === 'asc' ? va.localeCompare(vb as string) : (vb as string).localeCompare(va);
      }
      return sortDir === 'asc' ? (va as number) - (vb as number) : (vb as number) - (va as number);
    });
    return list;
  }, [positions, filter, sortKey, sortDir]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
  };

  const equityCurveData = portfolioData?.equity_history?.map((pt) => ({
    date: new Date(pt.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    value: pt.value,
  })) ?? [];

  const isLoading = portfolioLoading && positionsLoading;

  if (isLoading) return <PageLoader />;

  const totalPnl = positions.reduce((s, p) => s + p.unrealized_pnl, 0);

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title="Portfolio"
        subtitle={`${positions.length} open positions`}
        actions={
          <div className="flex items-center gap-4 text-sm">
            <div>
              <span className="text-text-secondary mr-2">Invested:</span>
              <span className="font-mono font-medium">
                {formatCurrency(
                  positions.reduce((s, p) => s + p.market_value, 0),
                  'USD',
                  true
                )}
              </span>
            </div>
            <div>
              <span className="text-text-secondary mr-2">Unrealized P&L:</span>
              <span className={cn('font-mono font-medium', pnlColor(totalPnl))}>
                {formatCurrency(totalPnl)}
              </span>
            </div>
          </div>
        }
      />

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Equity curve mini chart */}
        {equityCurveData.length > 1 && (
          <div className="bg-surface border border-border rounded-xl p-5">
            <h2 className="text-sm font-semibold text-text-primary mb-4">
              Equity Curve
            </h2>
            <ResponsiveContainer width="100%" height={160}>
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

        {/* Filter tabs */}
        <div className="flex items-center gap-1">
          {FILTER_TABS.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setFilter(key)}
              className={cn(
                'px-4 py-1.5 rounded-lg text-sm font-medium transition-colors',
                filter === key
                  ? 'bg-green-500/15 text-green-500'
                  : 'text-text-secondary hover:text-text-primary hover:bg-border'
              )}
            >
              {label}
              {key !== 'all' && (
                <span className="ml-1.5 text-xs opacity-60">
                  {positions.filter((p) => p.asset_type === key).length}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Positions table */}
        <div className="bg-surface border border-border rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  {(
                    [
                      { key: 'symbol', label: 'Symbol' },
                      { key: null, label: 'Type' },
                      { key: null, label: 'Side' },
                      { key: null, label: 'Qty' },
                      { key: null, label: 'Entry' },
                      { key: null, label: 'Current' },
                      { key: 'pnl', label: 'P&L' },
                      { key: 'pnl_pct', label: 'P&L %' },
                      { key: null, label: 'Strategy' },
                      { key: 'entry_date', label: 'Opened' },
                      { key: null, label: 'Actions' },
                    ] as { key: SortKey | null; label: string }[]
                  ).map(({ key, label }) => (
                    <th
                      key={label}
                      className={cn(
                        'px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider whitespace-nowrap',
                        key && 'cursor-pointer select-none hover:text-text-primary'
                      )}
                      onClick={() => key && handleSort(key)}
                    >
                      <span className="flex items-center gap-1">
                        {label}
                        {key && (
                          <ArrowUpDown className="w-3 h-3 opacity-50" />
                        )}
                      </span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {displayPositions.length === 0 ? (
                  <tr>
                    <td
                      colSpan={11}
                      className="text-center py-12 text-text-secondary"
                    >
                      No positions found
                    </td>
                  </tr>
                ) : (
                  displayPositions.map((position) => (
                    <PositionRow key={position.id} position={position} />
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

function PositionRow({ position }: { position: Position }) {
  const [closing, setClosing] = useState(false);

  const handleClose = async () => {
    setClosing(true);
    // Placeholder: would call POST /portfolio/positions/{id}/close
    await new Promise((r) => setTimeout(r, 800));
    setClosing(false);
  };

  return (
    <tr className="hover:bg-border/20 transition-colors">
      <td className="px-4 py-3 font-mono font-semibold text-text-primary whitespace-nowrap">
        {position.symbol}
      </td>
      <td className="px-4 py-3">
        <span className="text-xs px-1.5 py-0.5 rounded bg-border text-text-secondary capitalize">
          {position.asset_type}
        </span>
      </td>
      <td className="px-4 py-3">
        <span
          className={cn(
            'text-xs px-1.5 py-0.5 rounded capitalize font-medium',
            position.side === 'long'
              ? 'text-green-500 bg-green-500/10'
              : 'text-red-500 bg-red-500/10'
          )}
        >
          {position.side}
        </span>
      </td>
      <td className="px-4 py-3 font-mono text-text-primary">
        {position.quantity}
      </td>
      <td className="px-4 py-3 font-mono text-text-primary">
        {formatCurrency(position.entry_price)}
      </td>
      <td className="px-4 py-3 font-mono text-text-primary">
        {formatCurrency(position.current_price)}
      </td>
      <td className={cn('px-4 py-3 font-mono font-medium', pnlColor(position.unrealized_pnl))}>
        {formatCurrency(position.unrealized_pnl)}
      </td>
      <td className={cn('px-4 py-3 font-mono font-medium', pnlColor(position.unrealized_pnl_pct))}>
        {formatPercent(position.unrealized_pnl_pct)}
      </td>
      <td className="px-4 py-3 text-text-secondary text-xs">
        {position.strategy}
      </td>
      <td className="px-4 py-3 text-text-secondary text-xs whitespace-nowrap">
        {formatDate(position.opened_at)}
      </td>
      <td className="px-4 py-3">
        <button
          onClick={handleClose}
          disabled={closing}
          className="flex items-center gap-1 text-xs px-2.5 py-1.5 rounded bg-red-500/10 text-red-500 border border-red-500/20 hover:bg-red-500/20 disabled:opacity-50 transition-colors"
        >
          <X className="w-3 h-3" />
          {closing ? 'Closing…' : 'Close'}
        </button>
      </td>
    </tr>
  );
}
