"""Broker abstraction for Wall-E-T.

BrokerBase defines the interface. PaperBroker simulates order fills
using live market prices. ShoonyaBroker (Phase 3) will implement real trading.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import uuid4

from core.logger import JsonLogger


class BrokerBase(ABC):
    """Abstract broker interface."""

    @abstractmethod
    def place_order(
        self, symbol: str, exchange: str, side: str, qty: int,
        order_type: str = "MKT", price: float | None = None,
        trigger_price: float | None = None, product: str = "CNC",
    ) -> str | None:
        """Place an order. Returns order ID or None on failure."""
        ...

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        ...

    @abstractmethod
    def get_positions(self) -> list[dict]:
        ...

    @abstractmethod
    def get_order_book(self) -> list[dict]:
        ...


class PaperBroker(BrokerBase):
    """Simulates order execution for paper trading.

    Orders are filled immediately at the given price (market orders)
    or tracked until the price is hit (limit/SL orders).
    """

    def __init__(self, logger: JsonLogger):
        self.logger = logger
        self.orders: dict[str, dict] = {}
        self.positions: dict[str, dict] = {}  # symbol -> {qty, avg_price, product}

    def place_order(
        self, symbol: str, exchange: str, side: str, qty: int,
        order_type: str = "MKT", price: float | None = None,
        trigger_price: float | None = None, product: str = "CNC",
    ) -> str | None:
        order_id = f"PAPER-{uuid4().hex[:8].upper()}"
        now = datetime.now().isoformat()

        order = {
            "order_id": order_id,
            "symbol": symbol,
            "exchange": exchange,
            "side": side,
            "qty": qty,
            "order_type": order_type,
            "price": price,
            "trigger_price": trigger_price,
            "product": product,
            "status": "pending",
            "fill_price": None,
            "fill_time": None,
            "placed_at": now,
        }

        # Market orders fill immediately at the given price
        if order_type == "MKT" and price is not None:
            order["status"] = "filled"
            order["fill_price"] = price
            order["fill_time"] = now
            self._update_position(symbol, side, qty, price, product)

        self.orders[order_id] = order
        self.logger.info(
            "order_placed",
            order_id=order_id,
            symbol=symbol,
            side=side,
            qty=qty,
            price=price,
            status=order["status"],
            mode="paper",
        )
        return order_id

    def cancel_order(self, order_id: str) -> bool:
        if order_id in self.orders and self.orders[order_id]["status"] == "pending":
            self.orders[order_id]["status"] = "cancelled"
            return True
        return False

    def get_positions(self) -> list[dict]:
        return [
            {"symbol": sym, **pos}
            for sym, pos in self.positions.items()
            if pos["qty"] != 0
        ]

    def get_order_book(self) -> list[dict]:
        return list(self.orders.values())

    def check_pending_orders(self, symbol: str, current_price: float):
        """Check if any pending SL/limit orders should be filled at current price."""
        for order in self.orders.values():
            if order["symbol"] != symbol or order["status"] != "pending":
                continue

            filled = False
            if order["order_type"] == "SL-MKT" and order["trigger_price"]:
                # Stop-loss: triggers when price falls to/below trigger
                if order["side"] == "SELL" and current_price <= order["trigger_price"]:
                    filled = True
                elif order["side"] == "BUY" and current_price >= order["trigger_price"]:
                    filled = True

            if filled:
                order["status"] = "filled"
                order["fill_price"] = current_price
                order["fill_time"] = datetime.now().isoformat()
                self._update_position(
                    order["symbol"], order["side"], order["qty"],
                    current_price, order["product"],
                )
                self.logger.info(
                    "order_filled",
                    order_id=order["order_id"],
                    symbol=order["symbol"],
                    side=order["side"],
                    fill_price=current_price,
                    mode="paper",
                )

    def _update_position(self, symbol: str, side: str, qty: int, price: float, product: str):
        """Update position tracking after a fill."""
        if symbol not in self.positions:
            self.positions[symbol] = {"qty": 0, "avg_price": 0.0, "product": product}

        pos = self.positions[symbol]
        if side == "BUY":
            # Average up
            total_cost = pos["avg_price"] * pos["qty"] + price * qty
            pos["qty"] += qty
            pos["avg_price"] = total_cost / pos["qty"] if pos["qty"] > 0 else 0
        elif side == "SELL":
            pos["qty"] -= qty
            if pos["qty"] <= 0:
                pos["qty"] = 0
                pos["avg_price"] = 0.0

    def get_position_qty(self, symbol: str) -> int:
        """Get current position quantity for a symbol."""
        return self.positions.get(symbol, {}).get("qty", 0)

    def reset(self):
        """Reset all positions and orders (for new session)."""
        self.orders.clear()
        self.positions.clear()
