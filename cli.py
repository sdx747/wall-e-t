"""CLI entry point for Wall-E-T."""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import load_config, get_strategy_config
from core.logger import JsonLogger
from core.data import DataManager
from strategies import discover_strategies
from backtest.runner import BacktestRunner


def cmd_strategy_list(args, config, logger):
    """List all available strategies."""
    registry = discover_strategies()
    if not registry:
        print("No strategies found in strategies/ directory.")
        return

    print(f"\n{'Name':<25} {'Style':<12} {'Timeframe':<10} {'Version'}")
    print("─" * 60)
    for name, cls in sorted(registry.items()):
        print(f"{name:<25} {cls.style:<12} {cls.timeframe:<10} {cls.version}")
    print()


def cmd_strategy_info(args, config, logger):
    """Show details about a specific strategy."""
    registry = discover_strategies()
    if args.name not in registry:
        print(f"Strategy '{args.name}' not found. Run './wallet.sh strategy list' to see available strategies.")
        return

    cls = registry[args.name]
    strategy = cls()
    try:
        params = get_strategy_config(config, args.name)
        strategy.configure(params)
    except ValueError:
        print(f"(No config found for '{args.name}' in config.toml, showing defaults)\n")

    info = strategy.describe()
    print(f"\nStrategy: {info['name']} v{info['version']}")
    print(f"Style:    {info['style']}")
    print(f"Frame:    {info['timeframe']}")
    print(f"Lookback: {info['lookback']} candles")
    print(f"Symbols:  {', '.join(s for s, _ in info['watchlist']) if info['watchlist'] else 'None configured'}")
    print()


def cmd_data_fetch(args, config, logger):
    """Fetch historical data for a symbol."""
    dm = DataManager(config.get("data", {}), logger)
    exchange = args.exchange or config.get("data", {}).get("default_exchange", "NSE")

    print(f"Fetching {args.symbol} ({exchange}) from {args.start} to {args.end or 'today'}...")
    df = dm.fetch_historical(args.symbol, exchange, args.start, args.end, force=True)

    if df.empty:
        print("No data returned. Check the symbol name.")
    else:
        print(f"Fetched {len(df)} candles ({df.index[0].date()} to {df.index[-1].date()})")
        print(f"\nLatest 5 candles:")
        print(df.tail().to_string())


def cmd_data_list(args, config, logger):
    """List all cached data in the database."""
    dm = DataManager(config.get("data", {}), logger)
    cached = dm.list_cached_symbols()

    if not cached:
        print("No data cached. Run './wallet.sh data fetch <symbol>' to download data.")
        return

    print(f"\n{'Symbol':<15} {'Exchange':<10} {'Frame':<8} {'From':<12} {'To':<12} {'Candles'}")
    print("─" * 70)
    for item in cached:
        print(
            f"{item['symbol']:<15} {item['exchange']:<10} {item['timeframe']:<8} "
            f"{item['first_date'][:10]:<12} {item['last_date'][:10]:<12} {item['candles']}"
        )
    print()


def cmd_backtest(args, config, logger):
    """Run a backtest for a strategy."""
    registry = discover_strategies()
    if args.strategy not in registry:
        print(f"Strategy '{args.strategy}' not found.")
        return

    # Set up strategy
    cls = registry[args.strategy]
    strategy = cls()
    try:
        params = get_strategy_config(config, args.strategy)
    except ValueError:
        print(f"No config for strategy '{args.strategy}'. Add [strategy.{args.strategy}] to config.toml.")
        return

    strategy.configure(params)

    # Run backtest
    dm = DataManager(config.get("data", {}), logger)
    runner = BacktestRunner(dm, logger)
    capital = config.get("risk", {}).get("capital", 100_000)

    print(f"Running backtest: {args.strategy} ({args.start} to {args.end or 'today'})...")
    print(f"Capital: INR {capital:,.0f}")
    print(f"Symbols: {', '.join(s for s, _ in strategy.get_watchlist())}")
    print()

    result = runner.run(strategy, args.start, args.end or "", capital=capital)
    print(result.summary())

    # Show individual trades if verbose
    if args.verbose and result.trades:
        print(f"\n{'Symbol':<12} {'Entry':<12} {'Exit':<12} {'Entry Price':>12} {'Exit Price':>12} {'P&L':>10} {'P&L%':>8}")
        print("─" * 80)
        for t in result.trades:
            print(
                f"{t['symbol']:<12} {t['entry_date']:<12} {t['exit_date']:<12} "
                f"{t['entry_price']:>12.2f} {t['exit_price']:>12.2f} "
                f"{t['pnl']:>10.2f} {t['pnl_pct']:>7.2f}%"
            )
        print()


def cmd_logs(args, config, logger):
    """View log files."""
    from datetime import datetime as dt
    log_dir = Path(__file__).parent / "data" / "logs"

    if args.date:
        log_file = log_dir / f"{args.date}.jsonl"
    else:
        log_file = log_dir / f"{dt.now().strftime('%Y-%m-%d')}.jsonl"

    if not log_file.exists():
        print(f"No log file for {log_file.stem}.")
        return

    with open(log_file) as f:
        for line in f:
            try:
                record = json.loads(line)
                ts = record.get("timestamp", "")[:19]
                event = record.get("event", "")
                level = record.get("level", "info").upper()
                # Remove standard fields for display
                extra = {k: v for k, v in record.items() if k not in ("timestamp", "event", "level")}
                extra_str = json.dumps(extra, default=str) if extra else ""
                print(f"{ts}  [{level:<7}] {event:<25} {extra_str}")
            except json.JSONDecodeError:
                print(line.strip())


def cmd_status(args, config, logger):
    """Show current bot status."""
    print(f"\nWall-E-T Status")
    print("─" * 40)
    print(f"Mode:     {config.get('bot', {}).get('mode', 'unknown')}")
    print(f"Strategy: {config.get('bot', {}).get('active_strategy', 'none')}")
    print(f"Exchange: {config.get('data', {}).get('default_exchange', 'NSE')}")
    print()

    # Show cached data summary
    dm = DataManager(config.get("data", {}), logger)
    cached = dm.list_cached_symbols()
    print(f"Cached data: {len(cached)} symbol(s)")

    # Show available strategies
    registry = discover_strategies()
    print(f"Strategies:  {len(registry)} available ({', '.join(registry.keys())})")
    print()


def main():
    parser = argparse.ArgumentParser(
        prog="wall-e-t",
        description="Wall-E-T: Algo Trading Bot for Indian Markets",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # status
    subparsers.add_parser("status", help="Show bot status")

    # strategy
    strategy_parser = subparsers.add_parser("strategy", help="Manage strategies")
    strategy_sub = strategy_parser.add_subparsers(dest="action")
    strategy_sub.add_parser("list", help="List available strategies")
    info_parser = strategy_sub.add_parser("info", help="Show strategy details")
    info_parser.add_argument("name", help="Strategy name")

    # data
    data_parser = subparsers.add_parser("data", help="Manage market data")
    data_sub = data_parser.add_subparsers(dest="action")

    fetch_parser = data_sub.add_parser("fetch", help="Fetch historical data")
    fetch_parser.add_argument("symbol", help="Stock symbol (e.g., RELIANCE)")
    fetch_parser.add_argument("--exchange", default=None, help="Exchange (NSE or BSE)")
    fetch_parser.add_argument("--start", default="2024-01-01", help="Start date (YYYY-MM-DD)")
    fetch_parser.add_argument("--end", default=None, help="End date (YYYY-MM-DD)")

    data_sub.add_parser("list", help="List cached data")

    # backtest
    bt_parser = subparsers.add_parser("backtest", help="Run a backtest")
    bt_parser.add_argument("strategy", help="Strategy name")
    bt_parser.add_argument("--start", default="2024-01-01", help="Start date")
    bt_parser.add_argument("--end", default=None, help="End date")
    bt_parser.add_argument("-v", "--verbose", action="store_true", help="Show individual trades")

    # logs
    logs_parser = subparsers.add_parser("logs", help="View log files")
    logs_parser.add_argument("--date", default=None, help="Date (YYYY-MM-DD)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Load config
    try:
        config = load_config()
    except FileNotFoundError as e:
        print(str(e))
        return

    logger = JsonLogger(config.get("bot", {}).get("log_level", "info"))

    # Dispatch
    commands = {
        "status": cmd_status,
        "logs": cmd_logs,
    }

    if args.command == "strategy":
        if args.action == "list":
            cmd_strategy_list(args, config, logger)
        elif args.action == "info":
            cmd_strategy_info(args, config, logger)
        else:
            strategy_parser.print_help()
    elif args.command == "data":
        if args.action == "fetch":
            cmd_data_fetch(args, config, logger)
        elif args.action == "list":
            cmd_data_list(args, config, logger)
        else:
            data_parser.print_help()
    elif args.command == "backtest":
        cmd_backtest(args, config, logger)
    elif args.command in commands:
        commands[args.command](args, config, logger)
    else:
        parser.print_help()

    logger.close()


if __name__ == "__main__":
    main()
