"""Risk manager for Wall-E-T.

Every signal passes through here before execution.
Enforces position sizing, stop-losses, and daily loss limits.
"""

from core.logger import JsonLogger
from strategies.base import Signal, SignalType


class RiskManager:
    """Gates every order. Rejects or adjusts signals that violate risk rules."""

    def __init__(self, config: dict, logger: JsonLogger):
        self.logger = logger
        self.capital = config.get("capital", 100_000)
        self.risk_per_trade = config.get("risk_per_trade", 1.0) / 100
        self.max_daily_loss = config.get("max_daily_loss", 2.0) / 100
        self.max_open_positions = config.get("max_open_positions", 5)
        self.max_exposure_per_stock = config.get("max_exposure_per_stock", 20.0) / 100
        self.force_stop_loss = config.get("force_stop_loss", True)

        self.daily_pnl = 0.0
        self.open_position_count = 0
        self._trading_halted = False

    def check(self, signal: Signal, current_price: float) -> Signal | None:
        """Validate a signal. Returns adjusted signal or None if rejected."""
        # Daily loss limit
        if self._trading_halted:
            self.logger.warning(
                "signal_rejected", symbol=signal.symbol,
                reason="daily loss limit reached",
            )
            return None

        if signal.signal_type == SignalType.EXIT:
            # Always allow exits
            return signal

        # Require stop-loss on entries
        if self.force_stop_loss and signal.stop_loss is None:
            self.logger.warning(
                "signal_rejected", symbol=signal.symbol,
                reason="no stop-loss provided",
            )
            return None

        # Max open positions
        if self.open_position_count >= self.max_open_positions:
            self.logger.warning(
                "signal_rejected", symbol=signal.symbol,
                reason=f"max positions reached ({self.max_open_positions})",
            )
            return None

        # Position sizing based on risk per trade
        if signal.quantity is None and signal.stop_loss is not None:
            risk_amount = self.capital * self.risk_per_trade
            price_risk = abs(current_price - signal.stop_loss)
            if price_risk > 0:
                signal.quantity = int(risk_amount / price_risk)
            else:
                signal.quantity = 1

        # Cap exposure per stock
        if signal.quantity and current_price:
            max_qty = int((self.capital * self.max_exposure_per_stock) / current_price)
            if signal.quantity > max_qty:
                signal.quantity = max_qty
                self.logger.info(
                    "position_capped", symbol=signal.symbol,
                    capped_qty=max_qty, reason="max exposure per stock",
                )

        if signal.quantity and signal.quantity <= 0:
            self.logger.warning(
                "signal_rejected", symbol=signal.symbol,
                reason="calculated quantity is 0",
            )
            return None

        self.logger.debug(
            "signal_approved", symbol=signal.symbol,
            side=signal.side.value, qty=signal.quantity,
        )
        return signal

    def on_entry(self):
        """Called after a successful entry."""
        self.open_position_count += 1

    def on_exit(self, pnl: float):
        """Called after a successful exit. Updates daily P&L."""
        self.open_position_count = max(0, self.open_position_count - 1)
        self.daily_pnl += pnl

        if self.daily_pnl <= -(self.capital * self.max_daily_loss):
            self._trading_halted = True
            self.logger.warning(
                "trading_halted",
                daily_pnl=round(self.daily_pnl, 2),
                limit=round(self.capital * self.max_daily_loss, 2),
            )

    def reset_daily(self):
        """Reset daily counters. Call at start of each trading day."""
        self.daily_pnl = 0.0
        self._trading_halted = False

    def get_stats(self) -> dict:
        return {
            "daily_pnl": round(self.daily_pnl, 2),
            "open_positions": self.open_position_count,
            "trading_halted": self._trading_halted,
        }
