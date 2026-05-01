import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import type { Position, Signal } from './api';

interface Portfolio {
  value: number;
  cash: number;
  dayPnl: number;
  dayPnlPct: number;
  totalPnl: number;
  totalPnlPct: number;
  positions: Position[];
  equityHistory: { timestamp: string; value: number }[];
}

interface TradingStore {
  // State
  portfolio: Portfolio;
  signals: Signal[];
  prices: Record<string, number>;
  tradingMode: 'paper' | 'live';
  systemStatus: 'running' | 'paused' | 'halted';
  wsConnected: boolean;

  // Actions
  setPortfolio: (portfolio: Partial<Portfolio>) => void;
  setPositions: (positions: Position[]) => void;
  addSignal: (signal: Signal) => void;
  setSignals: (signals: Signal[]) => void;
  updatePrice: (symbol: string, price: number) => void;
  setPrices: (prices: Record<string, number>) => void;
  setTradingMode: (mode: 'paper' | 'live') => void;
  setSystemStatus: (status: 'running' | 'paused' | 'halted') => void;
  setWsConnected: (connected: boolean) => void;
}

const defaultPortfolio: Portfolio = {
  value: 0,
  cash: 0,
  dayPnl: 0,
  dayPnlPct: 0,
  totalPnl: 0,
  totalPnlPct: 0,
  positions: [],
  equityHistory: [],
};

export const useTradingStore = create<TradingStore>()(
  devtools(
    subscribeWithSelector((set) => ({
      // Initial state
      portfolio: defaultPortfolio,
      signals: [],
      prices: {},
      tradingMode: 'paper',
      systemStatus: 'running',
      wsConnected: false,

      // Actions
      setPortfolio: (partial) =>
        set((state) => ({
          portfolio: { ...state.portfolio, ...partial },
        })),

      setPositions: (positions) =>
        set((state) => ({
          portfolio: { ...state.portfolio, positions },
        })),

      addSignal: (signal) =>
        set((state) => ({
          // Keep latest 50 signals, newest first
          signals: [signal, ...state.signals].slice(0, 50),
        })),

      setSignals: (signals) => set({ signals }),

      updatePrice: (symbol, price) =>
        set((state) => ({
          prices: { ...state.prices, [symbol]: price },
        })),

      setPrices: (prices) => set({ prices }),

      setTradingMode: (tradingMode) => set({ tradingMode }),

      setSystemStatus: (systemStatus) => set({ systemStatus }),

      setWsConnected: (wsConnected) => set({ wsConnected }),
    })),
    { name: 'TradingStore' }
  )
);

// Selectors
export const selectPortfolioValue = (s: TradingStore) => s.portfolio.value;
export const selectDayPnl = (s: TradingStore) => s.portfolio.dayPnl;
export const selectPositions = (s: TradingStore) => s.portfolio.positions;
export const selectSignals = (s: TradingStore) => s.signals;
export const selectPrices = (s: TradingStore) => s.prices;
export const selectTradingMode = (s: TradingStore) => s.tradingMode;
export const selectSystemStatus = (s: TradingStore) => s.systemStatus;
