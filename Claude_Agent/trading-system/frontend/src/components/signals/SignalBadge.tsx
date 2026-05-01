import { cn } from '@/lib/utils';
import type { Signal } from '@/lib/api';

type SignalType = Signal['signal_type'];

interface SignalBadgeProps {
  type: SignalType;
  size?: 'sm' | 'md';
  className?: string;
}

const CONFIG: Record<
  SignalType,
  { label: string; classes: string }
> = {
  BUY: {
    label: 'BUY',
    classes: 'bg-green-500/15 text-green-500 border border-green-500/30',
  },
  SELL: {
    label: 'SELL',
    classes: 'bg-red-500/15 text-red-500 border border-red-500/30',
  },
  HOLD: {
    label: 'HOLD',
    classes: 'bg-border text-text-secondary border border-border',
  },
  BLOCK: {
    label: 'BLOCK',
    classes:
      'bg-transparent text-yellow-500 border border-yellow-500/60',
  },
  REDUCE: {
    label: 'REDUCE',
    classes: 'bg-yellow-500/10 text-yellow-500 border border-yellow-500/30',
  },
};

export function SignalBadge({ type, size = 'md', className }: SignalBadgeProps) {
  const { label, classes } = CONFIG[type] ?? CONFIG['HOLD'];
  return (
    <span
      className={cn(
        'inline-flex items-center justify-center rounded font-semibold font-mono tracking-wider',
        size === 'sm' ? 'text-xs px-1.5 py-0.5' : 'text-xs px-2.5 py-1',
        classes,
        className
      )}
    >
      {label}
    </span>
  );
}
