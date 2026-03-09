"""Backtest runner for Wall-E-T.

Runs a strategy against historical data and produces performance metrics.
Uses a simple vectorized approach with pandas — no heavy framework dependency.
"""

from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd

from core.data import DataManager
from core.logger import JsonLogger
from strategies.base import Strategy, SignalType, Side


@dataclass
class BacktestResult:
    """Results from a backtest run."""
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
    trades: list[dict]
    equity_curve: pd.Series

    def summary(self) -> str:
        """Human-readable summary of backtest results."""
        lines = [
            f"\n{'=' * 60}",
            f"  BACKTEST RESULTS: {self.strategy_name}",
            f"{'=' * 60}",
            f"  Period:           {self.start_date} to {self.end_date}",
            f"  Initial Capital:  INR {self.initial_capital:,.0f}",
            f"  Final Capital:    INR {self.final_capital:,.0f}",
            f"  Total Return:     {self.total_return_pct:+.2f}%",
            f"  CAGR:             {self.cagr_pct:+.2f}%",
            f"  Max Drawdown:     {self.max_drawdown_pct:.2f}%",
            f"  Sharpe Ratio:     {self.sharpe_ratio:.2f}",
            f"  Profit Factor:    {self.profit_factor:.2f}",
            f"{'─' * 60}",
            f"  Total Trades:     {self.total_trades}",
            f"  Winners:          {self.winning_trades}",
            f"  Losers:           {self.losing_trades}",
            f"  Win Rate:         {self.win_rate_pct:.1f}%",
            f"  Avg Win:          {self.avg_win_pct:+.2f}%",
            f"  Avg Loss:         {self.avg_loss_pct:+.2f}%",
            f"{'=' * 60}\n",
        ]
        return "\n".join(lines)


class BacktestRunner:
    """Runs strategies against historical data."""

    def __init__(self, data_manager: DataManager, logger: JsonLogger):
        self.data = data_manager
        self.logger = logger

    def run(
        self,
        strategy: Strategy,
        start: str,
        end: str,
        capital: float = 100_000,
        commission_pct: float = 0.05,
    ) -> BacktestResult:
        """Run a backtest for a strategy over a date range.

        Args:
            strategy: Configured Strategy instance.
            start: Start date "YYYY-MM-DD".
            end: End date "YYYY-MM-DD".
            capital: Initial capital in INR.
            commission_pct: Total transaction cost per trade as % (default 0.05% for statutory).

        Returns:
            BacktestResult with all metrics.
        """
        if not end:
            end = datetime.now().strftime("%Y-%m-%d")

        watchlist = strategy.get_watchlist()
        if not watchlist:
            raise ValueError("Strategy has no symbols in its watchlist.")

        self.logger.info(
            "backtest_start",
            strategy=strategy.name,
            start=start,
            end=end,
            capital=capital,
            symbols=[s for s, _ in watchlist],
        )

        # Fetch data for all symbols
        all_data: dict[str, pd.DataFrame] = {}
        for symbol, exchange in watchlist:
            df = self.data.fetch_historical(symbol, exchange, start, end)
            if not df.empty:
                all_data[symbol] = df

        if not all_data:
            raise ValueError("No data available for any symbol in the watchlist.")

        # Get all unique dates across symbols
        all_dates = sorted(set().union(*(df.index for df in all_data.values())))

        # Simulate
        cash = capital
        positions: dict[str, dict] = {}  # symbol -> {qty, entry_price, entry_date}
        trades: list[dict] = []
        equity_values: list[float] = []
        equity_dates: list = []

        for date in all_dates:
            # Run strategy on each symbol
            for symbol, exchange in watchlist:
                if symbol not in all_data:
                    continue

                df = all_data[symbol]
                # Get candles up to current date
                candles = df.loc[:date]
                if len(candles) < strategy.lookback():
                    continue

                signals = strategy.on_candle(symbol, candles)

                for signal in signals:
                    price = candles["close"].iloc[-1]
                    commission = price * (commission_pct / 100)

                    if signal.signal_type == SignalType.ENTRY and signal.side == Side.BUY:
                        # Skip if already in position
                        if symbol in positions:
                            continue

                        # Position sizing: allocate equal weight per stock
                        max_stocks = len(watchlist)
                        allocation = cash / max(1, max_stocks - len(positions))
                        qty = int(allocation / (price + commission))
                        if qty <= 0:
                            continue

                        cost = qty * (price + commission)
                        if cost > cash:
                            qty = int(cash / (price + commission))
                            cost = qty * (price + commission)
                        if qty <= 0:
                            continue

                        cash -= cost
                        positions[symbol] = {
                            "qty": qty,
                            "entry_price": price,
                            "entry_date": date,
                        }

                    elif signal.signal_type == SignalType.EXIT and signal.side == Side.SELL:
                        if symbol not in positions:
                            continue

                        pos = positions.pop(symbol)
                        proceeds = pos["qty"] * (price - commission)
                        cash += proceeds

                        pnl = (price - pos["entry_price"]) * pos["qty"]
                        pnl_pct = ((price / pos["entry_price"]) - 1) * 100

                        trades.append({
                            "symbol": symbol,
                            "entry_date": pos["entry_date"].strftime("%Y-%m-%d"),
                            "exit_date": date.strftime("%Y-%m-%d"),
                            "entry_price": round(pos["entry_price"], 2),
                            "exit_price": round(price, 2),
                            "quantity": pos["qty"],
                            "pnl": round(pnl, 2),
                            "pnl_pct": round(pnl_pct, 2),
                        })

            # Calculate portfolio value
            portfolio_value = cash
            for sym, pos in positions.items():
                if sym in all_data and date in all_data[sym].index:
                    portfolio_value += pos["qty"] * all_data[sym].loc[date, "close"]
                else:
                    portfolio_value += pos["qty"] * pos["entry_price"]

            equity_values.append(portfolio_value)
            equity_dates.append(date)

        # Close any remaining positions at last available price
        for symbol in list(positions.keys()):
            if symbol in all_data:
                last_price = all_data[symbol]["close"].iloc[-1]
                pos = positions.pop(symbol)
                cash += pos["qty"] * last_price
                pnl = (last_price - pos["entry_price"]) * pos["qty"]
                pnl_pct = ((last_price / pos["entry_price"]) - 1) * 100
                trades.append({
                    "symbol": symbol,
                    "entry_date": pos["entry_date"].strftime("%Y-%m-%d"),
                    "exit_date": all_data[symbol].index[-1].strftime("%Y-%m-%d"),
                    "entry_price": round(pos["entry_price"], 2),
                    "exit_price": round(last_price, 2),
                    "quantity": pos["qty"],
                    "pnl": round(pnl, 2),
                    "pnl_pct": round(pnl_pct, 2),
                    "note": "auto-closed at backtest end",
                })

        equity_curve = pd.Series(equity_values, index=equity_dates)
        final_capital = equity_values[-1] if equity_values else capital

        # Compute metrics
        result = self._compute_metrics(
            strategy.name, start, end, capital, final_capital,
            trades, equity_curve,
        )

        self.logger.info(
            "backtest_complete",
            strategy=strategy.name,
            total_return=result.total_return_pct,
            cagr=result.cagr_pct,
            sharpe=result.sharpe_ratio,
            trades=result.total_trades,
            win_rate=result.win_rate_pct,
        )

        return result

    def _compute_metrics(
        self,
        strategy_name: str,
        start: str,
        end: str,
        initial_capital: float,
        final_capital: float,
        trades: list[dict],
        equity_curve: pd.Series,
    ) -> BacktestResult:
        """Compute performance metrics from trades and equity curve."""
        total_return = ((final_capital / initial_capital) - 1) * 100

        # CAGR
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")
        years = max((end_dt - start_dt).days / 365.25, 0.01)
        cagr = ((final_capital / initial_capital) ** (1 / years) - 1) * 100

        # Max drawdown
        if not equity_curve.empty:
            rolling_max = equity_curve.cummax()
            drawdown = (equity_curve - rolling_max) / rolling_max * 100
            max_drawdown = abs(drawdown.min())
        else:
            max_drawdown = 0.0

        # Trade stats
        total_trades = len(trades)
        wins = [t for t in trades if t["pnl"] > 0]
        losses = [t for t in trades if t["pnl"] <= 0]
        winning_trades = len(wins)
        losing_trades = len(losses)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        avg_win = np.mean([t["pnl_pct"] for t in wins]) if wins else 0
        avg_loss = np.mean([t["pnl_pct"] for t in losses]) if losses else 0

        # Sharpe ratio (annualized, using daily returns)
        if len(equity_curve) > 1:
            daily_returns = equity_curve.pct_change().dropna()
            if daily_returns.std() > 0:
                sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
            else:
                sharpe = 0.0
        else:
            sharpe = 0.0

        # Profit factor
        gross_profit = sum(t["pnl"] for t in wins)
        gross_loss = abs(sum(t["pnl"] for t in losses))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float("inf")

        return BacktestResult(
            strategy_name=strategy_name,
            start_date=start,
            end_date=end,
            initial_capital=initial_capital,
            final_capital=round(final_capital, 2),
            total_return_pct=round(total_return, 2),
            cagr_pct=round(cagr, 2),
            max_drawdown_pct=round(max_drawdown, 2),
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate_pct=round(win_rate, 1),
            avg_win_pct=round(float(avg_win), 2),
            avg_loss_pct=round(float(avg_loss), 2),
            sharpe_ratio=round(float(sharpe), 2),
            profit_factor=round(float(profit_factor), 2),
            trades=trades,
            equity_curve=equity_curve,
        )
