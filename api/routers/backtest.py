"""Backtest endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_config, get_data_manager, get_logger
from api.models.backtest import (
    BacktestRequest,
    BacktestResponse,
    BacktestTradeItem,
    EquityPoint,
)
from backtest.runner import BacktestRunner
from core.config import get_strategy_config
from core.data import DataManager
from core.logger import JsonLogger
from strategies import discover_strategies

router = APIRouter(prefix="/api", tags=["backtest"])


@router.post("/backtest", response_model=BacktestResponse)
def run_backtest(
    req: BacktestRequest,
    config: dict = Depends(get_config),
    dm: DataManager = Depends(get_data_manager),
    logger: JsonLogger = Depends(get_logger),
):
    # Discover available strategies
    registry = discover_strategies()
    if req.strategy not in registry:
        raise HTTPException(
            status_code=404,
            detail=f"Strategy '{req.strategy}' not found. "
            f"Available: {list(registry.keys())}",
        )

    # Instantiate and configure the strategy
    strategy_cls = registry[req.strategy]
    strategy = strategy_cls()
    try:
        params = get_strategy_config(config, req.strategy)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"No config section [strategy.{req.strategy}] found in config.toml.",
        )
    strategy.configure(params)

    # Run the backtest
    runner = BacktestRunner(dm, logger)
    try:
        result = runner.run(
            strategy=strategy,
            start=req.start,
            end=req.end,
            capital=req.capital,
            commission_pct=req.commission_pct,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest failed: {e}")

    # Convert equity_curve pd.Series -> list[EquityPoint]
    equity_curve = [
        EquityPoint(date=idx.strftime("%Y-%m-%d"), value=round(val, 2))
        for idx, val in result.equity_curve.items()
    ]

    # Convert trades list[dict] -> list[BacktestTradeItem]
    trades = [BacktestTradeItem(**t) for t in result.trades]

    return BacktestResponse(
        strategy_name=result.strategy_name,
        start_date=result.start_date,
        end_date=result.end_date,
        initial_capital=result.initial_capital,
        final_capital=result.final_capital,
        total_return_pct=result.total_return_pct,
        cagr_pct=result.cagr_pct,
        max_drawdown_pct=result.max_drawdown_pct,
        total_trades=result.total_trades,
        winning_trades=result.winning_trades,
        losing_trades=result.losing_trades,
        win_rate_pct=result.win_rate_pct,
        avg_win_pct=result.avg_win_pct,
        avg_loss_pct=result.avg_loss_pct,
        sharpe_ratio=result.sharpe_ratio,
        profit_factor=result.profit_factor,
        equity_curve=equity_curve,
        trades=trades,
    )
