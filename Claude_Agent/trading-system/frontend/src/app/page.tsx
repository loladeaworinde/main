'use client';

import { useEffect, useCallback } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { useQuery } from '@tanstack/react-query';
import {
  TrendingUp,
  TrendingDown,
  Layers,
  Activity,
  DollarSign,
  BarChart2,
} from 'lucide-react';
import { getPortfolio, getPositions, getSignals } from '@/lib/api';
import wsManager from '@/lib/websocket';
import { useTradingStore } from '@/lib/store';
import { StatCard } from '@/components/ui/StatCard';
import { SignalBadge } from '@/components/signals/SignalBadge';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import {
  formatCurrency,
  formatPercent,
  formatTimestamp,
  pnlColor,
  generateClientId,
  cn,
} from '@/lib/utils';
import type { WSPriceUpdate, WSSignal, WSPortfolioUpdate } from '@/lib/websocket';
import type { Signal } from '@/lib/api';

const ALLOCATION_COLORS = ['#00d4aa', '#1e90ff', '#ffa502', '#ff4757', '#9b59b6', '#e67e22'];

export default function DashboardPage() {
  const {
    portfolio,
    signals,
    tradingMode,
    systemStatus,
    setPortfolio,
    addSignal,
    updatePrice,
    setSignals,
    setWsConnected,
  } = useTradingStore();

  // ── Queries ──────────────────────────────────────────────────────────────
  const { data: portfolioData, isLoading: portfolioLoading } = useQuery({
    queryKey: ['portfolio'],
    queryFn: getPortfolio,
    refetchInterval: 60_000,
  });

  const { data: positionsData } = useQuery({
    queryKey: ['positions'],
    queryFn: getPositions,
    refetchInterval: 30_000,
  });

  const { data: signalsData, isLoading: signalsLoading } = useQuery({
    queryKey: ['signals'],
    queryFn: () => getSignals(50),
    refetchInterval: 30_000,
  });

  // Sync server data into store
  useEffect(() => {
    if (portfolioData) {
      setPortfolio({
        value: portfolioData.total_value,
        cash: portfolioData.cash,
        dayPnl: portfolioData.day_pnl,
        dayPnlPct: portfolioData.day_pnl_pct,
        totalPnl: portfolioData.total_pnl,
        equityHistory: portfolioData.equity_history,
      });
    }
  }, [portfolioData, setPortfolio]);

  useEffect(() => {
    if (positionsData) {
      setPortfolio({ positions: positionsData });
    }
  }, [positionsData, setPortfolio]);

  useEffect(() => {
    if (signalsData) {
      setSignals(signalsData);
    }
  }, [signalsData, setSignals]);

  // ── WebSocket ─────────────────────────────────────────────────────────────
  const handlePriceUpdate = useCallback(
    (data: WSPriceUpdate) => {
      updatePrice(data.symbol, data.price);
    },
    [updatePrice]
  );

  const handleSignal = useCallback(
    (data: WSSignal) => {
      addSignal(data as Signal);
    },
    [addSignal]
  );

  const handlePortfolioUpdate = useCallback(
    (data: WSPortfolioUpdate) => {
      setPortfolio({
        value: data.total_value,
        cash: data.cash,
        dayPnl: data.day_pnl,
        dayPnlPct: data.day_pnl_pct,
        totalPnl: data.total_pnl,
      });
    },
    [setPortfolio]
  );

  useEffect(() => {
    const clientId = generateClientId();
    wsManager.connect(clientId);

    wsManager.subscribe<WSPriceUpdate>('price_update', handlePriceUpdate);
    wsManager.subscribe<WSSignal>('signal', handleSignal);
    wsManager.subscribe<WSPortfolioUpdate>('portfolio_update', handlePortfolioUpdate);

    const interval = setInterval(() => {
      setWsConnected(wsManager.isConnected);
    }, 2000);

    return () => {
      wsManager.unsubscribe('price_update', handlePriceUpdate);
      wsManager.unsubscribe('signal', handleSignal);
      wsManager.unsubscribe('portfolio_update', handlePortfolioUpdate);
      wsManager.disconnect();
      clearInterval(interval);
    };
  }, [handlePriceUpdate, handleSignal, handlePortfolioUpdate, setWsConnected]);

  // ── Allocation data for pie chart ─────────────────────────────────────────
  const positions = portfolio.positions;
  const allocationData = (() => {
    const groups: Record<string, number> = {};
    positions.forEach((p) => {
      const key = p.asset_type.charAt(0).toUpperCase() + p.asset_type.slice(1);
      groups[key] = (groups[key] || 0) + p.market_value;
    });
    if (portfolio.cash > 0) {
      groups['Cash'] = portfolio.cash;
    }
    return Object.entries(groups).map(([name, value]) => ({ name, value }));
  })();

  const recentSignals = signals.slice(0, 10);

  if (portfolioLoading && !portfolio.value) {
    return <PageLoader />;
  }

  return (
    <div className="p-6 space-y-6">
      {/* Page title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-text-primary">Dashboard</h1>
          <p className="text-sm text-text-secondary mt-0.5">
            Real-time portfolio overview and system status
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={cn(
              'text-xs font-semibold px-3 py-1.5 rounded-full',
              tradingMode === 'live'
                ? 'bg-red-500/20 text-red-500'
                : 'bg-blue-500/20 text-blue-500'
            )}
          >
            {tradingMode.toUpperCase()} MODE
          </span>
          <span
            className={cn(
              'text-xs font-semibold px-3 py-1.5 rounded-full',
              systemStatus === 'running'
                ? 'bg-green-500/20 text-green-500'
                : systemStatus === 'paused'
                ? 'bg-yellow-500/20 text-yellow-500'
                : 'bg-red-500/20 text-red-500'
            )}
          >
            {systemStatus.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Stat cards — 4-column grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard
          title="Portfolio Value"
          value={formatCurrency(portfolio.value, 'USD', true)}
          subValue={`${formatPercent(portfolio.dayPnlPct)} today`}
          subValueColor={portfolio.dayPnlPct >= 0 ? 'green' : 'red'}
          icon={<DollarSign className="w-4 h-4" />}
        />
        <StatCard
          title="Day P&L"
          value={formatCurrency(portfolio.dayPnl)}
          subValue={formatPercent(portfolio.dayPnlPct)}
          subValueColor={portfolio.dayPnl >= 0 ? 'green' : 'red'}
          icon={
            portfolio.dayPnl >= 0 ? (
              <TrendingUp className="w-4 h-4 text-green-500" />
            ) : (
              <TrendingDown className="w-4 h-4 text-red-500" />
            )
          }
        />
        <StatCard
          title="Open Positions"
          value={String(positions.length)}
          subValue={`${formatCurrency(
            positions.reduce((s, p) => s + p.market_value, 0),
            'USD',
            true
          )} invested`}
          subValueColor="neutral"
          icon={<Layers className="w-4 h-4" />}
        />
        <StatCard
          title="System Status"
          value={systemStatus.charAt(0).toUpperCase() + systemStatus.slice(1)}
          subValue={`${tradingMode.charAt(0).toUpperCase() + tradingMode.slice(1)} trading`}
          subValueColor={
            systemStatus === 'running'
              ? 'green'
              : systemStatus === 'paused'
              ? 'yellow'
              : 'red'
          }
          icon={<Activity className="w-4 h-4" />}
        />
      </div>

      {/* Bottom two-column layout */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Recent signals */}
        <div className="bg-surface border border-border rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-border flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BarChart2 className="w-4 h-4 text-text-secondary" />
              <h2 className="text-sm font-semibold text-text-primary">
                Recent Signals
              </h2>
            </div>
            <span className="text-xs text-text-secondary">
              {recentSignals.length} shown
            </span>
          </div>
          {signalsLoading && !recentSignals.length ? (
            <div className="p-6 text-center text-text-secondary text-sm">
              Loading signals…
            </div>
          ) : recentSignals.length === 0 ? (
            <div className="p-6 text-center text-text-secondary text-sm">
              No signals yet
            </div>
          ) : (
            <div className="divide-y divide-border">
              {recentSignals.map((signal) => (
                <div
                  key={signal.id}
                  className="flex items-center justify-between px-5 py-3 hover:bg-border/30 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <SignalBadge type={signal.signal_type} size="sm" />
                    <div>
                      <p className="text-sm font-mono font-medium text-text-primary">
                        {signal.symbol}
                      </p>
                      <p className="text-xs text-text-secondary">
                        {signal.strategy}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-mono text-text-primary">
                      {formatCurrency(signal.price)}
                    </p>
                    <p className="text-xs text-text-secondary">
                      {formatTimestamp(signal.timestamp)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Portfolio allocation pie chart */}
        <div className="bg-surface border border-border rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-border flex items-center gap-2">
            <Layers className="w-4 h-4 text-text-secondary" />
            <h2 className="text-sm font-semibold text-text-primary">
              Portfolio Allocation
            </h2>
          </div>
          {allocationData.length === 0 ? (
            <div className="flex items-center justify-center h-64 text-text-secondary text-sm">
              No positions open
            </div>
          ) : (
            <div className="p-4">
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={allocationData}
                    cx="50%"
                    cy="50%"
                    innerRadius={65}
                    outerRadius={100}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {allocationData.map((_, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={ALLOCATION_COLORS[index % ALLOCATION_COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#111111',
                      border: '1px solid #1f1f1f',
                      borderRadius: '8px',
                      color: '#f0f0f0',
                      fontSize: '12px',
                    }}
                    formatter={(value: number) => [
                      formatCurrency(value, 'USD', true),
                      '',
                    ]}
                  />
                  <Legend
                    iconType="circle"
                    iconSize={8}
                    formatter={(value) => (
                      <span style={{ color: '#888888', fontSize: '12px' }}>
                        {value}
                      </span>
                    )}
                  />
                </PieChart>
              </ResponsiveContainer>

              {/* Total value label */}
              <div className="text-center -mt-2">
                <p className="text-xs text-text-secondary">Total Invested</p>
                <p className="text-lg font-mono font-semibold text-text-primary">
                  {formatCurrency(
                    positions.reduce((s, p) => s + p.market_value, 0),
                    'USD',
                    true
                  )}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Total P&L summary bar */}
      <div className="bg-surface border border-border rounded-xl p-5 flex flex-wrap gap-6">
        <div>
          <p className="text-xs text-text-secondary uppercase tracking-wider mb-1">
            Total P&L (All-time)
          </p>
          <p className={cn('text-xl font-mono font-semibold', pnlColor(portfolio.totalPnl))}>
            {formatCurrency(portfolio.totalPnl)}
          </p>
        </div>
        <div>
          <p className="text-xs text-text-secondary uppercase tracking-wider mb-1">
            Cash Available
          </p>
          <p className="text-xl font-mono font-semibold text-text-primary">
            {formatCurrency(portfolio.cash, 'USD', true)}
          </p>
        </div>
        <div>
          <p className="text-xs text-text-secondary uppercase tracking-wider mb-1">
            Signals Today
          </p>
          <p className="text-xl font-mono font-semibold text-text-primary">
            {signals.filter((s) => {
              const today = new Date().toDateString();
              return new Date(s.timestamp).toDateString() === today;
            }).length}
          </p>
        </div>
        <div>
          <p className="text-xs text-text-secondary uppercase tracking-wider mb-1">
            Executed Today
          </p>
          <p className="text-xl font-mono font-semibold text-green-500">
            {signals.filter((s) => {
              const today = new Date().toDateString();
              return (
                s.status === 'executed' &&
                new Date(s.timestamp).toDateString() === today
              );
            }).length}
          </p>
        </div>
      </div>
    </div>
  );
}
