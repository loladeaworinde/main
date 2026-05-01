import { cn } from '@/lib/utils';

interface StatCardProps {
  title: string;
  value: string;
  subValue?: string;
  subValueColor?: 'green' | 'red' | 'yellow' | 'blue' | 'neutral';
  icon?: React.ReactNode;
  badge?: React.ReactNode;
  className?: string;
}

export function StatCard({
  title,
  value,
  subValue,
  subValueColor = 'neutral',
  icon,
  badge,
  className,
}: StatCardProps) {
  const subColors = {
    green: 'text-green-500',
    red: 'text-red-500',
    yellow: 'text-yellow-500',
    blue: 'text-blue-500',
    neutral: 'text-text-secondary',
  };

  return (
    <div
      className={cn(
        'bg-surface border border-border rounded-xl p-5',
        className
      )}
    >
      <div className="flex items-start justify-between mb-3">
        <p className="text-xs font-medium text-text-secondary uppercase tracking-wider">
          {title}
        </p>
        {icon && (
          <span className="text-text-secondary opacity-60">{icon}</span>
        )}
        {badge && badge}
      </div>
      <p className="text-2xl font-semibold text-text-primary font-mono">
        {value}
      </p>
      {subValue && (
        <p className={cn('text-sm mt-1 font-medium', subColors[subValueColor])}>
          {subValue}
        </p>
      )}
    </div>
  );
}
