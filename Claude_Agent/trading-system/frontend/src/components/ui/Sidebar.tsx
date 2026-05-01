'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Briefcase,
  Zap,
  BarChart2,
  FlaskConical,
  Settings,
  Activity,
  TrendingUp,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTradingStore } from '@/lib/store';

const navItems = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/portfolio', label: 'Portfolio', icon: Briefcase },
  { href: '/signals', label: 'Signals', icon: Zap },
  { href: '/charts', label: 'Charts', icon: BarChart2 },
  { href: '/backtest', label: 'Backtest', icon: FlaskConical },
  { href: '/settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const tradingMode = useTradingStore((s) => s.tradingMode);
  const systemStatus = useTradingStore((s) => s.systemStatus);
  const wsConnected = useTradingStore((s) => s.wsConnected);

  return (
    <aside className="w-56 flex-shrink-0 bg-surface border-r border-border flex flex-col">
      {/* Logo */}
      <div className="px-4 py-5 border-b border-border">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-6 h-6 text-green-500" />
          <span className="font-semibold text-text-primary tracking-tight">
            AlgoTrader
          </span>
        </div>
        <p className="text-xs text-text-secondary mt-1">Quantitative Platform</p>
      </div>

      {/* Status badges */}
      <div className="px-4 py-3 border-b border-border flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <span className="text-xs text-text-secondary">Mode</span>
          <span
            className={cn(
              'text-xs font-semibold px-2 py-0.5 rounded',
              tradingMode === 'live'
                ? 'bg-red-500/20 text-red-500'
                : 'bg-blue-500/20 text-blue-500'
            )}
          >
            {tradingMode.toUpperCase()}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-text-secondary">System</span>
          <span
            className={cn(
              'text-xs font-semibold px-2 py-0.5 rounded',
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
        <div className="flex items-center justify-between">
          <span className="text-xs text-text-secondary">Live Feed</span>
          <div className="flex items-center gap-1.5">
            <span
              className={cn(
                'w-2 h-2 rounded-full',
                wsConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
              )}
            />
            <span className="text-xs text-text-secondary">
              {wsConnected ? 'Connected' : 'Offline'}
            </span>
          </div>
        </div>
      </div>

      {/* Nav links */}
      <nav className="flex-1 px-2 py-4 space-y-1">
        {navItems.map(({ href, label, icon: Icon }) => {
          const isActive =
            href === '/' ? pathname === '/' : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-green-500/10 text-green-500'
                  : 'text-text-secondary hover:bg-border hover:text-text-primary'
              )}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-border">
        <div className="flex items-center gap-2">
          <Activity className="w-3.5 h-3.5 text-text-secondary" />
          <span className="text-xs text-text-secondary">
            {new Date().toLocaleDateString('en-US', {
              weekday: 'short',
              month: 'short',
              day: 'numeric',
            })}
          </span>
        </div>
      </div>
    </aside>
  );
}
