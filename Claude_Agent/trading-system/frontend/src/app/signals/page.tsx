'use client';

import { useState, useEffect, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getSignals } from '@/lib/api';
import type { Signal } from '@/lib/api';
import wsManager from '@/lib/websocket';
import { useTradingStore } from '@/lib/store';
import { SignalBadge } from '@/components/signals/SignalBadge';
import { PageHeader } from '@/components/ui/PageHeader';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { formatCurrency, formatDateTime, sentimentColor, cn } from '@/lib/utils';
import type { WSSignal } from '@/lib/websocket';
import { Zap, RefreshCw } from 'lucide-react';

type StatusFilter = 'all' | 'executed' | 'blocked' | 'pending';

const STATUS_TABS: { key: StatusFilter; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'executed', label: 'Executed' },
  { key: 'blocked', label: 'Blocked' },
  { key: 'pending', label: 'Pending' },
];

const STATUS_BADGE: Record<Signal['status'], { label: string; classes: string }> = {
  executed: {
    label: 'Executed',
    classes: 'bg-green-500/10 text-green-500',
  },
  blocked: {
    label: 'Blocked',
    classes: 'bg-red-500/10 text-red-500',
  },
  pending: {
    label: 'Pending',
    classes: 'bg-yellow-500/10 text-yellow-500',
  },
  expired: {
    label: 'Expired',
    classes: 'bg-border text-text-secondary',
  },
};

export default function SignalsPage() {
  const { signals, addSignal, setSignals } = useTradingStore();
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [newCount, setNewCount] = useState(0);

  const { isLoading, refetch } = useQuery({
    queryKey: ['signals-full'],
    queryFn: () => getSignals(200),
    onSuccess: (data) => setSignals(data),
  });

  // WebSocket live updates
  const handleWsSignal = useCallback(
    (data: WSSignal) => {
      addSignal(data as Signal);
      setNewCount((c) => c + 1);
    },
    [addSignal]
  );

  useEffect(() => {
    wsManager.subscribe<WSSignal>('signal', handleWsSignal);
    return () => wsManager.unsubscribe('signal', handleWsSignal);
  }, [handleWsSignal]);

  const filteredSignals =
    statusFilter === 'all'
      ? signals
      : signals.filter((s) => s.status === statusFilter);

  if (isLoading && !signals.length) return <PageLoader />;

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title="Signals Log"
        subtitle="Real-time algorithmic trading signals"
        actions={
          <div className="flex items-center gap-3">
            {newCount > 0 && (
              <span className="text-xs bg-green-500/20 text-green-500 px-2.5 py-1 rounded-full font-medium animate-pulse">
                +{newCount} new
              </span>
            )}
            <button
              onClick={() => {
                refetch();
                setNewCount(0);
              }}
              className="flex items-center gap-2 text-xs px-3 py-2 rounded-lg border border-border text-text-secondary hover:text-text-primary hover:border-border/60 transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh
            </button>
          </div>
        }
      />

      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {/* Summary chips */}
        <div className="flex flex-wrap gap-3">
          {(['executed', 'blocked', 'pending', 'expired'] as const).map((s) => {
            const count = signals.filter((sig) => sig.status === s).length;
            const cfg = STATUS_BADGE[s];
            return (
              <div
                key={s}
                className={cn(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium',
                  cfg.classes
                )}
              >
                <span className="capitalize">{s}</span>
                <span className="font-mono font-bold">{count}</span>
              </div>
            );
          })}
        </div>

        {/* Filter tabs */}
        <div className="flex items-center gap-1">
          {STATUS_TABS.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setStatusFilter(key)}
              className={cn(
                'px-4 py-1.5 rounded-lg text-sm font-medium transition-colors',
                statusFilter === key
                  ? 'bg-green-500/15 text-green-500'
                  : 'text-text-secondary hover:text-text-primary hover:bg-border'
              )}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Signals table */}
        <div className="bg-surface border border-border rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  {[
                    'Time',
                    'Symbol',
                    'Signal',
                    'Strategy',
                    'Price',
                    'Strength',
                    'Sentiment',
                    'Status',
                  ].map((h) => (
                    <th
                      key={h}
                      className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider whitespace-nowrap"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredSignals.length === 0 ? (
                  <tr>
                    <td
                      colSpan={8}
                      className="text-center py-12 text-text-secondary"
                    >
                      <div className="flex flex-col items-center gap-2">
                        <Zap className="w-8 h-8 opacity-20" />
                        <span>No signals found</span>
                      </div>
                    </td>
                  </tr>
                ) : (
                  filteredSignals.map((signal, idx) => (
                    <SignalRow key={signal.id ?? idx} signal={signal} />
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

function SignalRow({ signal }: { signal: Signal }) {
  const statusCfg = STATUS_BADGE[signal.status] ?? STATUS_BADGE.expired;
  const sentColor = sentimentColor(signal.sentiment_score);
  const sentimentPct = Math.round(
    ((signal.sentiment_score + 1) / 2) * 100
  );

  return (
    <tr className="hover:bg-border/20 transition-colors">
      {/* Time */}
      <td className="px-4 py-3 text-xs text-text-secondary font-mono whitespace-nowrap">
        {formatDateTime(signal.timestamp)}
      </td>
      {/* Symbol */}
      <td className="px-4 py-3">
        <div>
          <p className="font-mono font-semibold text-text-primary">
            {signal.symbol}
          </p>
          <p className="text-xs text-text-secondary capitalize">
            {signal.asset_type}
          </p>
        </div>
      </td>
      {/* Signal badge */}
      <td className="px-4 py-3">
        <SignalBadge type={signal.signal_type} />
      </td>
      {/* Strategy */}
      <td className="px-4 py-3 text-text-secondary text-xs">
        {signal.strategy}
      </td>
      {/* Price */}
      <td className="px-4 py-3 font-mono text-text-primary">
        {formatCurrency(signal.price)}
      </td>
      {/* Strength bar */}
      <td className="px-4 py-3">
        <div className="flex items-center gap-2 min-w-[80px]">
          <div className="flex-1 h-1.5 bg-border rounded-full overflow-hidden">
            <div
              className={cn(
                'h-full rounded-full transition-all',
                signal.strength >= 70
                  ? 'bg-green-500'
                  : signal.strength >= 40
                  ? 'bg-yellow-500'
                  : 'bg-red-500'
              )}
              style={{ width: `${signal.strength}%` }}
            />
          </div>
          <span className="text-xs font-mono text-text-secondary w-6 text-right">
            {signal.strength}
          </span>
        </div>
      </td>
      {/* Sentiment */}
      <td className="px-4 py-3">
        <div className="flex items-center gap-2 min-w-[80px]">
          <div className="flex-1 h-1.5 bg-border rounded-full overflow-hidden">
            <div
              className="h-full rounded-full bg-blue-500 transition-all"
              style={{ width: `${sentimentPct}%` }}
            />
          </div>
          <span className={cn('text-xs font-mono w-8 text-right', sentColor)}>
            {signal.sentiment_score.toFixed(2)}
          </span>
        </div>
      </td>
      {/* Status */}
      <td className="px-4 py-3">
        <span
          className={cn(
            'text-xs px-2 py-0.5 rounded font-medium',
            statusCfg.classes
          )}
        >
          {statusCfg.label}
        </span>
      </td>
    </tr>
  );
}
