"""Dashboard-related Pydantic models."""

from pydantic import BaseModel


class DashboardMetrics(BaseModel):
    total_pnl: float = 0.0
    today_pnl: float = 0.0
    open_positions_count: int = 0
    total_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    max_drawdown_pct: float = 0.0
    capital: float = 0.0
    mode: str = "paper"
    active_strategy: str = ""
    trading_halted: bool = False


class DailyPnL(BaseModel):
    date: str
    pnl: float
    cumulative_pnl: float
