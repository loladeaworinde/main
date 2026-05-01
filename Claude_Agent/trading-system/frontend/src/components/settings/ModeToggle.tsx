'use client';

import { useState } from 'react';
import { AlertTriangle, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTradingStore } from '@/lib/store';
import { toggleTradingMode } from '@/lib/api';

interface ModeToggleProps {
  className?: string;
}

export function ModeToggle({ className }: ModeToggleProps) {
  const tradingMode = useTradingStore((s) => s.tradingMode);
  const setTradingMode = useTradingStore((s) => s.setTradingMode);
  const [showModal, setShowModal] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleToggleClick = () => {
    if (tradingMode === 'paper') {
      // Switching to live — show confirmation modal
      setShowModal(true);
    } else {
      // Switching to paper — no confirmation needed
      doSwitch('paper');
    }
  };

  const doSwitch = async (mode: 'paper' | 'live') => {
    setIsLoading(true);
    setError(null);
    try {
      await toggleTradingMode(mode);
      setTradingMode(mode);
      setShowModal(false);
    } catch {
      setError('Failed to switch trading mode. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* Toggle button */}
      <div className={cn('flex items-center gap-4', className)}>
        <span className="text-sm text-text-secondary">Trading Mode</span>
        <button
          onClick={handleToggleClick}
          disabled={isLoading}
          className={cn(
            'relative inline-flex items-center w-20 h-8 rounded-full border transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-background disabled:opacity-50',
            tradingMode === 'live'
              ? 'bg-red-500/20 border-red-500/40 focus:ring-red-500'
              : 'bg-blue-500/20 border-blue-500/40 focus:ring-blue-500'
          )}
          aria-label={`Switch to ${tradingMode === 'paper' ? 'live' : 'paper'} trading`}
          role="switch"
          aria-checked={tradingMode === 'live'}
        >
          <span
            className={cn(
              'absolute flex items-center justify-center w-14 h-6 rounded-full text-xs font-bold transition-all duration-200',
              tradingMode === 'live'
                ? 'right-0.5 bg-red-500 text-white'
                : 'left-0.5 bg-blue-500 text-white'
            )}
          >
            {tradingMode === 'live' ? 'LIVE' : 'PAPER'}
          </span>
        </button>
      </div>

      {/* Confirmation modal */}
      {showModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-title"
        >
          <div className="bg-surface border border-border rounded-xl p-6 max-w-sm w-full mx-4 shadow-2xl">
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-red-500/15 flex items-center justify-center">
                  <AlertTriangle className="w-5 h-5 text-red-500" />
                </div>
                <h2
                  id="modal-title"
                  className="text-base font-semibold text-text-primary"
                >
                  Switch to Live Trading
                </h2>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="text-text-secondary hover:text-text-primary transition-colors p-1"
                aria-label="Close modal"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Warning */}
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 mb-5">
              <p className="text-sm text-red-400 leading-relaxed">
                Switching to <strong>LIVE mode</strong> will execute real trades
                with real money. All signals will be routed to your connected
                broker accounts.
              </p>
            </div>

            <p className="text-sm text-text-secondary mb-5">
              Ensure your risk parameters are configured correctly before
              proceeding. This action cannot be undone mid-trade.
            </p>

            {error && (
              <p className="text-sm text-red-500 mb-4 bg-red-500/10 p-2 rounded">
                {error}
              </p>
            )}

            {/* Actions */}
            <div className="flex gap-3">
              <button
                onClick={() => setShowModal(false)}
                disabled={isLoading}
                className="flex-1 px-4 py-2.5 rounded-lg border border-border text-sm font-medium text-text-secondary hover:text-text-primary hover:border-border/80 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => doSwitch('live')}
                disabled={isLoading}
                className="flex-1 px-4 py-2.5 rounded-lg bg-red-500 text-white text-sm font-semibold hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? 'Switching…' : 'Confirm — Go Live'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
