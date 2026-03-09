export interface DashboardMetrics {
  total_pnl: number;
  total_pnl_pct: number;
  today_pnl: number;
  today_pnl_pct: number;
  win_rate: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  open_positions: number;
  capital_deployed: number;
  total_capital: number;
}

export interface DailyPnL {
  date: string;
  pnl: number;
  cumulative_pnl: number;
  trades: number;
}

export interface Position {
  symbol: string;
  exchange: string;
  qty: number;
  avg_price: number;
  current_price: number;
  unrealized_pnl: number;
  pnl_pct: number;
  entry_time: string;
  strategy: string;
}

export interface Trade {
  id: number;
  symbol: string;
  exchange: string;
  side: "BUY" | "SELL";
  entry_price: number;
  exit_price: number;
  qty: number;
  pnl: number;
  pnl_pct: number;
  entry_time: string;
  exit_time: string;
  strategy: string;
  fees: number;
}

export interface TradeFilter {
  symbol?: string;
  strategy?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  per_page?: number;
  sort?: string;
  order?: "asc" | "desc";
}

export interface TradeListResponse {
  trades: Trade[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface BacktestRequest {
  strategy: string;
  start_date: string;
  end_date: string;
  capital: number;
}

export interface BacktestTrade {
  symbol: string;
  side: "BUY" | "SELL";
  entry_price: number;
  exit_price: number;
  qty: number;
  pnl: number;
  pnl_pct: number;
  entry_time: string;
  exit_time: string;
}

export interface EquityPoint {
  date: string;
  equity: number;
}

export interface BacktestResponse {
  total_return: number;
  total_return_pct: number;
  cagr: number;
  max_drawdown: number;
  sharpe_ratio: number;
  profit_factor: number;
  win_rate: number;
  total_trades: number;
  avg_win: number;
  avg_loss: number;
  equity_curve: EquityPoint[];
  trades: BacktestTrade[];
}

export interface StrategyInfo {
  name: string;
  version: string;
  style: string;
  timeframe: string;
  active: boolean;
  watchlist: string[];
}

export interface StrategyDetail extends StrategyInfo {
  description: string;
  config: Record<string, unknown>;
}

export interface CachedSymbol {
  symbol: string;
  exchange: string;
  last_updated: string;
}

export interface ConfigInfo {
  mode: "PAPER" | "LIVE";
  version: string;
  broker: string;
  strategies: string[];
}
