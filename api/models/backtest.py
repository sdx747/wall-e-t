"""Backtest-related Pydantic models."""

from pydantic import BaseModel, Field


class BacktestRequest(BaseModel):
    strategy: str
    start: str = Field(description="Start date YYYY-MM-DD")
    end: str = Field(description="End date YYYY-MM-DD")
    capital: float = 100_000
    commission_pct: float = 0.05


class EquityPoint(BaseModel):
    date: str
    value: float


class BacktestTradeItem(BaseModel):
    symbol: str
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    quantity: int
    pnl: float
    pnl_pct: float
    note: str | None = None


class BacktestResponse(BaseModel):
    strategy_name: str
    start_date: str
    end_date: str
    initial_capital: float
    final_capital: float
    total_return_pct: float
    cagr_pct: float
    max_drawdown_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    avg_win_pct: float
    avg_loss_pct: float
    sharpe_ratio: float
    profit_factor: float
    equity_curve: list[EquityPoint]
    trades: list[BacktestTradeItem]
