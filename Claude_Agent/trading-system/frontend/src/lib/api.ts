import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('[API Error]', error.response?.status, error.message);
    return Promise.reject(error);
  }
);

// ── TypeScript Interfaces ──────────────────────────────────────────────────

export interface Position {
  id: string;
  symbol: string;
  asset_type: 'stock' | 'option' | 'crypto';
  side: 'long' | 'short';
  quantity: number;
  entry_price: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  strategy: string;
  opened_at: string;
}

export interface PortfolioSummary {
  total_value: number;
  cash: number;
  invested: number;
  day_pnl: number;
  day_pnl_pct: number;
  total_pnl: number;
  total_pnl_pct: number;
  positions_count: number;
  equity_history: { timestamp: string; value: number }[];
}

export interface Signal {
  id: string;
  symbol: string;
  asset_type: 'stock' | 'option' | 'crypto';
  signal_type: 'BUY' | 'SELL' | 'HOLD' | 'BLOCK' | 'REDUCE';
  strategy: string;
  strength: number; // 0–100
  sentiment_score: number; // -1 to 1
  price: number;
  timestamp: string;
  status: 'executed' | 'blocked' | 'pending' | 'expired';
  reason?: string;
}

export interface OHLCVBar {
  time: number; // Unix timestamp (seconds)
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface BacktestParams {
  symbol: string;
  start_date: string;
  end_date: string;
  strategies: string[];
  initial_capital: number;
  asset_type: 'stock' | 'option' | 'crypto';
}

export interface BacktestTrade {
  id: string;
  symbol: string;
  side: 'long' | 'short';
  entry_date: string;
  exit_date: string;
  entry_price: number;
  exit_price: number;
  quantity: number;
  pnl: number;
  pnl_pct: number;
  strategy: string;
}

export interface BacktestResult {
  id: string;
  symbol: string;
  strategies: string[];
  start_date: string;
  end_date: string;
  initial_capital: number;
  final_capital: number;
  total_return: number;
  total_return_pct: number;
  sharpe_ratio: number;
  max_drawdown: number;
  max_drawdown_pct: number;
  win_rate: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  avg_win: number;
  avg_loss: number;
  profit_factor: number;
  equity_curve: { timestamp: string; value: number }[];
  trades: BacktestTrade[];
  created_at: string;
}

export interface SentimentResult {
  symbol: string;
  score: number; // -1 to 1
  label: 'very_bearish' | 'bearish' | 'neutral' | 'bullish' | 'very_bullish';
  sources: {
    news: number;
    social: number;
    analyst: number;
  };
  support_levels: number[];
  resistance_levels: number[];
  updated_at: string;
}

export interface SystemSettings {
  trading_mode: 'paper' | 'live';
  system_status: 'running' | 'paused' | 'halted';
  risk: {
    max_position_size_pct: number;
    max_portfolio_heat_pct: number;
    max_daily_loss_pct: number;
    max_drawdown_pct: number;
  };
  strategy_weights: Record<string, number>;
  brokers: {
    robinhood: { connected: boolean; status: string };
    webull: { connected: boolean; status: string };
    alpaca: { connected: boolean; status: string };
  };
}

// ── API Functions ──────────────────────────────────────────────────────────

export async function getPortfolio(): Promise<PortfolioSummary> {
  const { data } = await apiClient.get<PortfolioSummary>('/portfolio/summary');
  return data;
}

export async function getPositions(): Promise<Position[]> {
  const { data } = await apiClient.get<Position[]>('/portfolio/positions');
  return data;
}

export async function getSignals(limit = 20): Promise<Signal[]> {
  const { data } = await apiClient.get<Signal[]>('/signals', {
    params: { limit },
  });
  return data;
}

export async function getOHLCV(
  symbol: string,
  timeframe: string
): Promise<OHLCVBar[]> {
  const { data } = await apiClient.get<OHLCVBar[]>(
    `/data/ohlcv/${encodeURIComponent(symbol)}`,
    { params: { timeframe } }
  );
  return data;
}

export async function getBacktestResults(): Promise<BacktestResult[]> {
  const { data } = await apiClient.get<BacktestResult[]>('/backtest/results');
  return data;
}

export async function runBacktest(params: BacktestParams): Promise<BacktestResult> {
  const { data } = await apiClient.post<BacktestResult>('/backtest/run', params);
  return data;
}

export async function toggleTradingMode(
  mode: 'paper' | 'live'
): Promise<{ success: boolean; mode: string }> {
  const { data } = await apiClient.post('/settings/mode', { mode });
  return data;
}

export async function getSentiment(symbol: string): Promise<SentimentResult> {
  const { data } = await apiClient.get<SentimentResult>(
    `/analysis/sentiment/${encodeURIComponent(symbol)}`
  );
  return data;
}

export async function getSettings(): Promise<SystemSettings> {
  const { data } = await apiClient.get<SystemSettings>('/settings');
  return data;
}

export default apiClient;
