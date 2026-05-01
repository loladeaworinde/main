import { cn, formatCurrency, formatPercent, pnlColor } from '@/lib/utils';
import type { Position } from '@/lib/api';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface PositionCardProps {
  position: Position;
  onClose?: (position: Position) => void;
  className?: string;
}

export function PositionCard({ position, onClose, className }: PositionCardProps) {
  const isProfit = position.unrealized_pnl >= 0;

  return (
    <div
      className={cn(
        'bg-surface border border-border rounded-xl p-4',
        className
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-semibold text-text-primary font-mono">
              {position.symbol}
            </span>
            <span className="text-xs px-1.5 py-0.5 rounded bg-border text-text-secondary capitalize">
              {position.asset_type}
            </span>
            <span
              className={cn(
                'text-xs px-1.5 py-0.5 rounded capitalize',
                position.side === 'long'
                  ? 'bg-green-500/10 text-green-500'
                  : 'bg-red-500/10 text-red-500'
              )}
            >
              {position.side}
            </span>
          </div>
          <p className="text-xs text-text-secondary mt-1">{position.strategy}</p>
        </div>
        {/* Large P&L */}
        <div className="text-right">
          <div
            className={cn(
              'flex items-center gap-1 text-xl font-semibold font-mono',
              pnlColor(position.unrealized_pnl)
            )}
          >
            {isProfit ? (
              <TrendingUp className="w-4 h-4" />
            ) : (
              <TrendingDown className="w-4 h-4" />
            )}
            {formatCurrency(position.unrealized_pnl)}
          </div>
          <p
            className={cn(
              'text-sm font-medium font-mono',
              pnlColor(position.unrealized_pnl_pct)
            )}
          >
            {formatPercent(position.unrealized_pnl_pct)}
          </p>
        </div>
      </div>

      {/* Price info */}
      <div className="grid grid-cols-3 gap-3 mb-3">
        <div>
          <p className="text-xs text-text-secondary mb-0.5">Entry</p>
          <p className="text-sm font-mono text-text-primary">
            {formatCurrency(position.entry_price)}
          </p>
        </div>
        <div>
          <p className="text-xs text-text-secondary mb-0.5">Current</p>
          <p className="text-sm font-mono text-text-primary">
            {formatCurrency(position.current_price)}
          </p>
        </div>
        <div>
          <p className="text-xs text-text-secondary mb-0.5">Qty</p>
          <p className="text-sm font-mono text-text-primary">
            {position.quantity}
          </p>
        </div>
      </div>

      {/* Market value + close button */}
      <div className="flex items-center justify-between pt-2 border-t border-border">
        <div>
          <span className="text-xs text-text-secondary">Market Value: </span>
          <span className="text-sm font-mono text-text-primary">
            {formatCurrency(position.market_value)}
          </span>
        </div>
        {onClose && (
          <button
            onClick={() => onClose(position)}
            className="text-xs px-3 py-1.5 rounded bg-red-500/10 text-red-500 border border-red-500/20 hover:bg-red-500/20 transition-colors font-medium"
          >
            Close
          </button>
        )}
      </div>
    </div>
  );
}
