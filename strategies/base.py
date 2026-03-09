"""Base strategy interface for Wall-E-T.

All trading strategies must subclass Strategy and implement the required methods.
Strategies return Signal objects — they never interact with the broker directly.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum

import pandas as pd


class Side(Enum):
    BUY = "BUY"
    SELL = "SELL"


class SignalType(Enum):
    ENTRY = "entry"
    EXIT = "exit"
    STOP_UPDATE = "stop_update"


@dataclass
class Signal:
    """A trade signal emitted by a strategy.

    Strategies produce signals; the risk manager and executor decide
    whether and how to act on them.
    """
    symbol: str
    exchange: str
    side: Side
    signal_type: SignalType
    quantity: int | None = None     # None = let risk manager decide
    price: float | None = None      # None = market order
    stop_loss: float | None = None
    target: float | None = None
    product: str = "CNC"            # CNC (delivery), MIS (intraday), NRML (F&O)
    reason: str = ""                # Human-readable reason for audit log
    metadata: dict = field(default_factory=dict)  # Strategy-specific data


class Strategy(ABC):
    """Abstract base class for all trading strategies.

    To create a new strategy:
      1. Create a new file in strategies/ (e.g., strategies/my_strategy.py)
      2. Subclass Strategy
      3. Set the class attributes (name, version, style, timeframe)
      4. Implement configure(), on_candle(), and get_watchlist()
      5. Done — the strategy is auto-discovered and available via CLI

    Example:
        class MyStrategy(Strategy):
            name = "my_strategy"
            version = "1.0"
            style = "swing"
            timeframe = "1d"

            def configure(self, params: dict) -> None:
                self.fast = params.get("fast_period", 9)

            def on_candle(self, symbol, candles):
                # Your logic here
                return [Signal(...)] or []

            def get_watchlist(self):
                return self._symbols
    """

    name: str = "unnamed"
    version: str = "1.0"
    style: str = "swing"        # "intraday", "swing", "positional"
    timeframe: str = "1d"       # Primary candle timeframe

    def __init__(self):
        self._symbols: list[tuple[str, str]] = []

    @abstractmethod
    def configure(self, params: dict) -> None:
        """Called once at startup with strategy-specific params from config.toml.

        Use this to set indicator periods, thresholds, and the symbol watchlist.
        """
        ...

    @abstractmethod
    def on_candle(self, symbol: str, candles: pd.DataFrame) -> list[Signal]:
        """Called on every new candle close. Return zero or more signals.

        Args:
            symbol: The stock symbol (e.g., "RELIANCE").
            candles: DataFrame with columns [open, high, low, close, volume],
                     indexed by datetime, most recent last.
                     Length is at least self.lookback() candles.

        Returns:
            List of Signal objects. Empty list = no action.
        """
        ...

    @abstractmethod
    def get_watchlist(self) -> list[tuple[str, str]]:
        """Return list of (symbol, exchange) tuples to watch.

        Example: [("RELIANCE", "NSE"), ("INFY", "NSE")]
        """
        ...

    def on_tick(self, symbol: str, tick: dict) -> list[Signal]:
        """Optional: called on every live tick. Override for tick-level logic."""
        return []

    def on_order_update(self, order: dict) -> list[Signal]:
        """Optional: called when an order status changes."""
        return []

    def lookback(self) -> int:
        """How many candles the strategy needs for indicator computation.

        DataManager will pre-fetch at least this many candles.
        """
        return 200

    def describe(self) -> dict:
        """Return a description of the strategy for CLI display."""
        return {
            "name": self.name,
            "version": self.version,
            "style": self.style,
            "timeframe": self.timeframe,
            "watchlist": self.get_watchlist(),
            "lookback": self.lookback(),
        }
