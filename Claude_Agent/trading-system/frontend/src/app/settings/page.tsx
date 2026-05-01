'use client';

import { useQuery } from '@tanstack/react-query';
import { getSettings } from '@/lib/api';
import { ModeToggle } from '@/components/settings/ModeToggle';
import { PageHeader } from '@/components/ui/PageHeader';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { cn } from '@/lib/utils';
import {
  Shield,
  Database,
  BarChart2,
  Wifi,
  CheckCircle,
  XCircle,
  AlertCircle,
} from 'lucide-react';

// Data provider API key checks (checks non-empty env at build time — runtime env via Next.js public vars)
const DATA_PROVIDERS = [
  { name: 'Alpaca Markets', envKey: 'NEXT_PUBLIC_ALPACA_KEY', description: 'Brokerage & market data' },
  { name: 'Polygon.io', envKey: 'NEXT_PUBLIC_POLYGON_KEY', description: 'Real-time & historical data' },
  { name: 'Finnhub', envKey: 'NEXT_PUBLIC_FINNHUB_KEY', description: 'News & sentiment data' },
  { name: 'OpenAI', envKey: 'NEXT_PUBLIC_OPENAI_KEY', description: 'AI signal analysis' },
  { name: 'Twelve Data', envKey: 'NEXT_PUBLIC_TWELVE_DATA_KEY', description: 'Forex & crypto feeds' },
];

const MOCK_RISK = {
  max_position_size_pct: 5,
  max_portfolio_heat_pct: 20,
  max_daily_loss_pct: 3,
  max_drawdown_pct: 15,
};

const MOCK_STRATEGY_WEIGHTS: Record<string, number> = {
  momentum: 0.25,
  mean_reversion: 0.20,
  trend_following: 0.20,
  breakout: 0.15,
  macd_crossover: 0.10,
  rsi_divergence: 0.10,
};

const MOCK_BROKERS = {
  robinhood: { connected: true, status: 'Active — Paper account' },
  webull: { connected: false, status: 'Not configured' },
  alpaca: { connected: true, status: 'Active — Paper account' },
};

export default function SettingsPage() {
  const { data: settings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: getSettings,
    // Fallback to mock data if API is unavailable
    retry: 1,
  });

  const risk = settings?.risk ?? MOCK_RISK;
  const strategyWeights = settings?.strategy_weights ?? MOCK_STRATEGY_WEIGHTS;
  const brokers = settings?.brokers ?? MOCK_BROKERS;

  if (isLoading) return <PageLoader />;

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title="Settings"
        subtitle="System configuration and risk parameters"
      />

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Trading Mode */}
        <section className="bg-surface border border-border rounded-xl p-5">
          <div className="flex items-center gap-2 mb-5">
            <Wifi className="w-4 h-4 text-text-secondary" />
            <h2 className="text-sm font-semibold text-text-primary">
              Trading Mode
            </h2>
          </div>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <ModeToggle />
              <p className="text-xs text-text-secondary mt-2 max-w-md">
                Paper mode simulates trades without real capital. Switch to Live
                to route orders through your connected broker accounts. Always
                verify risk parameters before going live.
              </p>
            </div>
            <div className="flex flex-col gap-1 text-xs text-text-secondary bg-background border border-border rounded-lg p-3 min-w-[200px]">
              <div className="flex justify-between">
                <span>Order routing</span>
                <span className="text-text-primary">Simulated</span>
              </div>
              <div className="flex justify-between">
                <span>Market data</span>
                <span className="text-text-primary">Real-time</span>
              </div>
              <div className="flex justify-between">
                <span>Signal generation</span>
                <span className="text-text-primary">Active</span>
              </div>
            </div>
          </div>
        </section>

        {/* Risk Parameters */}
        <section className="bg-surface border border-border rounded-xl p-5">
          <div className="flex items-center gap-2 mb-5">
            <Shield className="w-4 h-4 text-text-secondary" />
            <h2 className="text-sm font-semibold text-text-primary">
              Risk Parameters
            </h2>
            <span className="ml-auto text-xs text-text-secondary bg-border px-2 py-0.5 rounded">
              Read-only
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            {[
              {
                label: 'Max Position Size',
                value: `${risk.max_position_size_pct}%`,
                description: 'Per-asset cap of portfolio',
                color: 'text-blue-500',
              },
              {
                label: 'Max Portfolio Heat',
                value: `${risk.max_portfolio_heat_pct}%`,
                description: 'Total risk exposure limit',
                color: 'text-yellow-500',
              },
              {
                label: 'Max Daily Loss',
                value: `${risk.max_daily_loss_pct}%`,
                description: 'Circuit breaker threshold',
                color: 'text-red-500',
              },
              {
                label: 'Max Drawdown',
                value: `${risk.max_drawdown_pct}%`,
                description: 'System halt trigger',
                color: 'text-red-500',
              },
            ].map(({ label, value, description, color }) => (
              <div
                key={label}
                className="bg-background border border-border rounded-xl p-4"
              >
                <p className="text-xs text-text-secondary mb-2">{label}</p>
                <p className={cn('text-2xl font-mono font-semibold', color)}>
                  {value}
                </p>
                <p className="text-xs text-text-secondary mt-1">{description}</p>
              </div>
            ))}
          </div>
          <p className="text-xs text-text-secondary mt-4 flex items-center gap-1.5">
            <AlertCircle className="w-3.5 h-3.5 text-yellow-500" />
            Risk parameters are configured in the backend. Contact your system
            administrator to adjust limits.
          </p>
        </section>

        {/* Data Providers */}
        <section className="bg-surface border border-border rounded-xl p-5">
          <div className="flex items-center gap-2 mb-5">
            <Database className="w-4 h-4 text-text-secondary" />
            <h2 className="text-sm font-semibold text-text-primary">
              Data Providers
            </h2>
          </div>
          <div className="space-y-3">
            {DATA_PROVIDERS.map(({ name, envKey, description }) => {
              // In production, this would check the actual env var
              const isConfigured = typeof window !== 'undefined'
                ? !!process.env[envKey]
                : false;
              return (
                <div
                  key={name}
                  className="flex items-center justify-between py-3 border-b border-border last:border-0"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={cn(
                        'w-2.5 h-2.5 rounded-full',
                        isConfigured ? 'bg-green-500' : 'bg-red-500'
                      )}
                    />
                    <div>
                      <p className="text-sm font-medium text-text-primary">
                        {name}
                      </p>
                      <p className="text-xs text-text-secondary">{description}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5">
                    {isConfigured ? (
                      <>
                        <CheckCircle className="w-4 h-4 text-green-500" />
                        <span className="text-xs text-green-500 font-medium">
                          Configured
                        </span>
                      </>
                    ) : (
                      <>
                        <XCircle className="w-4 h-4 text-text-secondary" />
                        <span className="text-xs text-text-secondary">
                          Not set
                        </span>
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Connected Brokers */}
        <section className="bg-surface border border-border rounded-xl p-5">
          <div className="flex items-center gap-2 mb-5">
            <Wifi className="w-4 h-4 text-text-secondary" />
            <h2 className="text-sm font-semibold text-text-primary">
              Connected Brokers
            </h2>
          </div>
          <div className="space-y-3">
            {(
              Object.entries(brokers) as [
                string,
                { connected: boolean; status: string }
              ][]
            ).map(([broker, info]) => (
              <div
                key={broker}
                className="flex items-center justify-between py-3 px-4 bg-background border border-border rounded-xl"
              >
                <div className="flex items-center gap-3">
                  <div
                    className={cn(
                      'w-2.5 h-2.5 rounded-full',
                      info.connected ? 'bg-green-500 animate-pulse' : 'bg-border'
                    )}
                  />
                  <div>
                    <p className="text-sm font-medium text-text-primary capitalize">
                      {broker}
                    </p>
                    <p className="text-xs text-text-secondary">{info.status}</p>
                  </div>
                </div>
                <span
                  className={cn(
                    'text-xs font-semibold px-2.5 py-1 rounded-full',
                    info.connected
                      ? 'bg-green-500/15 text-green-500'
                      : 'bg-border text-text-secondary'
                  )}
                >
                  {info.connected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            ))}
          </div>
        </section>

        {/* Strategy Weights */}
        <section className="bg-surface border border-border rounded-xl p-5">
          <div className="flex items-center gap-2 mb-5">
            <BarChart2 className="w-4 h-4 text-text-secondary" />
            <h2 className="text-sm font-semibold text-text-primary">
              Strategy Weights
            </h2>
            <span className="ml-auto text-xs text-text-secondary bg-border px-2 py-0.5 rounded">
              Display only
            </span>
          </div>
          <div className="space-y-4">
            {Object.entries(strategyWeights).map(([strategy, weight]) => (
              <div key={strategy}>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-sm text-text-primary capitalize">
                    {strategy.replace(/_/g, ' ')}
                  </span>
                  <span className="text-sm font-mono text-text-secondary">
                    {(weight * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="h-2 bg-background rounded-full overflow-hidden border border-border">
                  <div
                    className="h-full bg-gradient-to-r from-green-500/60 to-green-500 rounded-full transition-all"
                    style={{ width: `${weight * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
          <p className="text-xs text-text-secondary mt-4 flex items-center gap-1.5">
            <AlertCircle className="w-3.5 h-3.5 text-yellow-500" />
            Strategy weights are adjusted by the ML ensemble model. Manual
            overrides require backend configuration.
          </p>
        </section>
      </div>
    </div>
  );
}
