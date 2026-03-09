"""Trading engine for Wall-E-T.

The central orchestrator. Fetches data, runs the strategy,
passes signals through risk management, and executes orders.
"""

import time
from datetime import datetime

import pytz

from core.broker import PaperBroker, ShoonyaBroker
from core.config import load_config, get_strategy_config
from core.data import DataManager
from core.logger import JsonLogger
from core.notifier import Notifier
from core.portfolio import PortfolioTracker
from core.risk import RiskManager
from strategies import discover_strategies
from strategies.base import Side, SignalType

IST = pytz.timezone("Asia/Kolkata")


class TradingEngine:
    """Wires everything together and runs the main trading loop."""

    def __init__(self, config: dict):
        self.config = config
        self.mode = config.get("bot", {}).get("mode", "paper")
        self.logger = JsonLogger(config.get("bot", {}).get("log_level", "info"))

        # Core modules
        self.data = DataManager(config.get("data", {}), self.logger)
        self.risk = RiskManager(config.get("risk", {}), self.logger)
        self.notifier = Notifier(config.get("telegram", {}), self.logger)

        # Broker selection based on mode
        if self.mode == "live":
            self.broker = ShoonyaBroker(config.get("broker", {}), self.logger)
        else:
            self.broker = PaperBroker(self.logger)

        self.portfolio = PortfolioTracker(
            config.get("data", {}).get("db_path", "data/history.db"),
            self.logger,
            mode=self.mode,
        )

        # Load strategy
        strategy_name = config.get("bot", {}).get("active_strategy", "")
        registry = discover_strategies()
        if strategy_name not in registry:
            raise ValueError(f"Strategy '{strategy_name}' not found. Available: {list(registry.keys())}")

        self.strategy = registry[strategy_name]()
        strategy_params = get_strategy_config(config, strategy_name)
        self.strategy.configure(strategy_params)

        self._running = False

        # Schedule config
        sched = config.get("schedule", {})
        self.market_open = sched.get("market_open", "09:15")
        self.market_close = sched.get("market_close", "15:30")

    def start(self):
        """Start the trading engine. Runs until interrupted."""
        # Login to broker if live mode
        if self.mode == "live":
            if not self.broker.login():
                print("ERROR: Broker login failed. Check credentials in config.toml.")
                return

        self.logger.info(
            "engine_start",
            mode=self.mode,
            strategy=self.strategy.name,
            symbols=[s for s, _ in self.strategy.get_watchlist()],
        )
        self._running = True
        self.risk.reset_daily()
        self.notifier.send(
            f"🤖 *Wall-E-T started*\nMode: {self.mode}\nStrategy: {self.strategy.name}"
        )

        print(f"\nWall-E-T started in {self.mode.upper()} mode")
        print(f"Strategy: {self.strategy.name}")
        print(f"Symbols:  {', '.join(s for s, _ in self.strategy.get_watchlist())}")
        print(f"Market hours: {self.market_open} - {self.market_close} IST")
        print("Press Ctrl+C to stop\n")

        try:
            while self._running:
                now = datetime.now(IST)

                if not self._is_market_hours(now):
                    if now.hour >= int(self.market_close.split(":")[0]):
                        # After market close — run end-of-day, then wait for next day
                        self._end_of_day()
                        self._wait_until_market_open()
                    else:
                        # Before market open
                        self._wait_until_market_open()
                    continue

                self._run_cycle()

                # Wait before next cycle (strategy timeframe dependent)
                interval = self._get_interval()
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.stop()

    def stop(self):
        """Graceful shutdown."""
        self._running = False
        self._print_summary()

        # Logout from broker if live
        if self.mode == "live" and hasattr(self.broker, "logout"):
            self.broker.logout()

        self.notifier.send("🛑 *Wall-E-T stopped*")
        self.logger.info("engine_stop", mode=self.mode)
        self.logger.close()

    def run_once(self):
        """Run a single cycle — useful for testing."""
        self.risk.reset_daily()
        self._run_cycle()
        self._print_summary()

    def _run_cycle(self):
        """One iteration: fetch data → run strategy → process signals."""
        watchlist = self.strategy.get_watchlist()

        for symbol, exchange in watchlist:
            # Fetch latest candles
            candles = self.data.get_candles(
                symbol, exchange,
                timeframe=self.strategy.timeframe,
                n=self.strategy.lookback(),
            )

            if candles.empty or len(candles) < self.strategy.lookback():
                continue

            current_price = candles["close"].iloc[-1]

            # Check pending SL orders
            self.broker.check_pending_orders(symbol, current_price)

            # Run strategy
            signals = self.strategy.on_candle(symbol, candles)

            for signal in signals:
                # Risk check
                approved = self.risk.check(signal, current_price)
                if approved is None:
                    continue

                self._execute_signal(approved, current_price)

    def _execute_signal(self, signal, current_price: float):
        """Execute an approved signal."""
        if signal.signal_type == SignalType.ENTRY and signal.side == Side.BUY:
            if self.portfolio.has_position(signal.symbol):
                return  # Already in position

            order_id = self.broker.place_order(
                symbol=signal.symbol,
                exchange=signal.exchange,
                side="BUY",
                qty=signal.quantity,
                order_type="MKT",
                price=current_price,
                product=signal.product,
            )

            if order_id:
                self.portfolio.open_position(
                    signal.symbol, signal.exchange,
                    signal.quantity, current_price,
                    self.strategy.name,
                )
                # Record order (PaperBroker stores in .orders dict, ShoonyaBroker doesn't)
                order_data = (
                    self.broker.orders.get(order_id, {})
                    if hasattr(self.broker, "orders") else
                    {"order_id": order_id, "symbol": signal.symbol, "side": "BUY",
                     "qty": signal.quantity, "price": current_price, "status": "filled",
                     "placed_at": datetime.now().isoformat()}
                )
                self.portfolio.record_order(order_data, self.strategy.name, signal.reason)
                self.risk.on_entry()
                self.notifier.trade_alert(
                    signal.symbol, "BUY", signal.quantity, current_price, signal.reason,
                )

                # Place stop-loss order if provided
                if signal.stop_loss:
                    self.broker.place_order(
                        symbol=signal.symbol,
                        exchange=signal.exchange,
                        side="SELL",
                        qty=signal.quantity,
                        order_type="SL-MKT",
                        trigger_price=signal.stop_loss,
                        product=signal.product,
                    )

        elif signal.signal_type == SignalType.EXIT and signal.side == Side.SELL:
            if not self.portfolio.has_position(signal.symbol):
                return

            pos = self.portfolio.positions[signal.symbol]
            order_id = self.broker.place_order(
                symbol=signal.symbol,
                exchange=signal.exchange,
                side="SELL",
                qty=pos["qty"],
                order_type="MKT",
                price=current_price,
                product=signal.product,
            )

            if order_id:
                entry_price = pos["avg_price"]
                pnl = self.portfolio.close_position(signal.symbol, current_price)
                order_data = (
                    self.broker.orders.get(order_id, {})
                    if hasattr(self.broker, "orders") else
                    {"order_id": order_id, "symbol": signal.symbol, "side": "SELL",
                     "qty": pos["qty"], "price": current_price, "status": "filled",
                     "placed_at": datetime.now().isoformat()}
                )
                self.portfolio.record_order(order_data, self.strategy.name, signal.reason)
                self.risk.on_exit(pnl)
                self.notifier.trade_closed(
                    signal.symbol, entry_price, current_price, pos["qty"], pnl,
                )

    def _is_market_hours(self, now: datetime) -> bool:
        """Check if current time is within market hours (weekday only)."""
        if now.weekday() >= 5:  # Saturday, Sunday
            return False

        open_h, open_m = map(int, self.market_open.split(":"))
        close_h, close_m = map(int, self.market_close.split(":"))

        market_open = now.replace(hour=open_h, minute=open_m, second=0)
        market_close = now.replace(hour=close_h, minute=close_m, second=0)

        return market_open <= now <= market_close

    def _wait_until_market_open(self):
        """Sleep until next market open. Checks every 60s to allow clean exit."""
        print("Waiting for market hours...")
        while self._running:
            now = datetime.now(IST)
            if self._is_market_hours(now):
                self.risk.reset_daily()
                print(f"Market open — starting trading cycle at {now.strftime('%H:%M:%S')}")
                return
            time.sleep(60)

    def _end_of_day(self):
        """End-of-day summary."""
        stats = self.risk.get_stats()
        positions = self.portfolio.get_positions()
        trades_today = self.portfolio.get_today_trades()
        self.logger.info(
            "end_of_day",
            daily_pnl=stats["daily_pnl"],
            open_positions=len(positions),
        )
        self.notifier.daily_summary({
            **stats,
            "open_positions": len(positions),
            "trades_today": len(trades_today),
        })
        self._print_summary()

    def _get_interval(self) -> int:
        """Get sleep interval in seconds based on strategy timeframe."""
        tf = self.strategy.timeframe
        intervals = {"1m": 60, "5m": 300, "15m": 900, "1h": 3600, "1d": 300}
        return intervals.get(tf, 300)

    def _print_summary(self):
        """Print current status."""
        positions = self.portfolio.get_positions()
        stats = self.risk.get_stats()

        print(f"\n{'─' * 50}")
        print(f"  Daily P&L: INR {stats['daily_pnl']:+,.2f}")
        print(f"  Open positions: {len(positions)}")
        for pos in positions:
            print(f"    {pos['symbol']}: {pos['qty']} @ {pos['avg_price']:.2f}")
        print(f"  Trading halted: {'Yes' if stats['trading_halted'] else 'No'}")
        print(f"{'─' * 50}\n")
