"""Broker abstraction for Wall-E-T.

BrokerBase defines the interface. PaperBroker simulates order fills.
ShoonyaBroker connects to Shoonya (Finvasia) for real trading.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from hashlib import sha256
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


# Product type mapping: our names -> Shoonya's codes
_PRODUCT_MAP = {"CNC": "C", "MIS": "I", "NRML": "M"}
_PRODUCT_MAP_REV = {v: k for k, v in _PRODUCT_MAP.items()}

# Order type mapping
_ORDER_TYPE_MAP = {"MKT": "MKT", "LMT": "LMT", "SL-MKT": "SL-MKT", "SL-LMT": "SL-LMT"}


class ShoonyaBroker(BrokerBase):
    """Real broker implementation using Shoonya (Finvasia) API.

    Requires NorenRestApiPy package and a Shoonya trading account.
    """

    # Shoonya API endpoints
    HOST = "https://api.shoonya.com/NorenWClientTP/"
    WEBSOCKET = "wss://api.shoonya.com/NorenWSTP/"

    def __init__(self, config: dict, logger: JsonLogger):
        self.logger = logger
        self.config = config
        self._api = None
        self._logged_in = False

    def login(self) -> bool:
        """Authenticate with Shoonya. Returns True on success."""
        try:
            from NorenRestApiPy.NorenApi import NorenApi
        except ImportError:
            self.logger.error("broker_error", error="NorenRestApiPy not installed. Run: pip install NorenRestApiPy")
            return False

        # Create API instance
        self._api = NorenApi(host=self.HOST, websocket=self.WEBSOCKET)

        # Generate TOTP if secret is provided
        totp_code = self.config.get("twoFA", "")
        totp_secret = self.config.get("totp_secret", "")
        if totp_secret and not totp_code:
            try:
                import pyotp
                totp_code = pyotp.TOTP(totp_secret).now()
            except ImportError:
                self.logger.error("broker_error", error="pyotp not installed for auto-TOTP. Run: pip install pyotp")
                return False

        resp = self._api.login(
            userid=self.config["user_id"],
            password=self.config["password"],
            twoFA=totp_code,
            vendor_code=self.config.get("vendor_code", ""),
            api_secret=self.config.get("api_secret", ""),
            imei=self.config.get("imei", "abc1234"),
        )

        if resp and resp.get("stat") == "Ok":
            self._logged_in = True
            self.logger.info("broker_login", status="success", user=self.config["user_id"])
            return True

        error = resp.get("emsg", "Unknown error") if resp else "No response from broker"
        self.logger.error("broker_login", status="failed", error=error)
        return False

    def place_order(
        self, symbol: str, exchange: str, side: str, qty: int,
        order_type: str = "MKT", price: float | None = None,
        trigger_price: float | None = None, product: str = "CNC",
    ) -> str | None:
        if not self._logged_in:
            self.logger.error("broker_error", error="Not logged in")
            return None

        resp = self._api.place_order(
            buy_or_sell="B" if side == "BUY" else "S",
            product_type=_PRODUCT_MAP.get(product, "C"),
            exchange=exchange,
            tradingsymbol=symbol,
            quantity=qty,
            discloseqty=0,
            price_type=_ORDER_TYPE_MAP.get(order_type, "MKT"),
            price=price or 0.0,
            trigger_price=trigger_price,
            retention="DAY",
        )

        if resp and resp.get("stat") == "Ok":
            order_id = resp.get("norenordno", "")
            self.logger.info(
                "order_placed",
                order_id=order_id,
                symbol=symbol,
                side=side,
                qty=qty,
                order_type=order_type,
                price=price,
                mode="live",
            )
            return order_id

        error = resp.get("emsg", "Unknown error") if resp else "No response"
        self.logger.error("order_failed", symbol=symbol, side=side, error=error)
        return None

    def cancel_order(self, order_id: str) -> bool:
        if not self._logged_in:
            return False

        resp = self._api.cancel_order(orderno=order_id)
        if resp and resp.get("stat") == "Ok":
            self.logger.info("order_cancelled", order_id=order_id)
            return True

        error = resp.get("emsg", "Unknown error") if resp else "No response"
        self.logger.error("cancel_failed", order_id=order_id, error=error)
        return False

    def get_positions(self) -> list[dict]:
        if not self._logged_in:
            return []

        resp = self._api.get_positions()
        if not resp:
            return []

        positions = []
        for pos in resp:
            net_qty = int(pos.get("netqty", 0))
            if net_qty == 0:
                continue
            positions.append({
                "symbol": pos.get("tsym", ""),
                "exchange": pos.get("exch", ""),
                "qty": net_qty,
                "avg_price": float(pos.get("netavgprc", 0)),
                "product": _PRODUCT_MAP_REV.get(pos.get("prd", ""), "CNC"),
                "pnl": float(pos.get("rpnl", 0)) + float(pos.get("urmtom", 0)),
            })
        return positions

    def get_order_book(self) -> list[dict]:
        if not self._logged_in:
            return []

        resp = self._api.get_order_book()
        if not resp:
            return []

        orders = []
        for order in resp:
            orders.append({
                "order_id": order.get("norenordno", ""),
                "symbol": order.get("tsym", ""),
                "exchange": order.get("exch", ""),
                "side": "BUY" if order.get("trantype") == "B" else "SELL",
                "qty": int(order.get("qty", 0)),
                "price": float(order.get("prc", 0)),
                "trigger_price": float(order.get("trgprc", 0)) if order.get("trgprc") else None,
                "order_type": order.get("prctyp", ""),
                "product": _PRODUCT_MAP_REV.get(order.get("prd", ""), "CNC"),
                "status": order.get("status", ""),
                "fill_price": float(order.get("flprc", 0)) if order.get("flprc") else None,
            })
        return orders

    def get_margins(self) -> dict:
        """Get available margins/limits."""
        if not self._logged_in:
            return {}

        resp = self._api.get_limits()
        if not resp:
            return {}

        return {
            "cash": float(resp.get("cash", 0)),
            "margin_used": float(resp.get("marginused", 0)),
            "margin_available": float(resp.get("marginused", 0)),
        }

    def search_symbol(self, exchange: str, query: str) -> list[dict]:
        """Search for a trading symbol."""
        if not self._logged_in:
            return []

        resp = self._api.searchscrip(exchange=exchange, searchtext=query)
        if not resp or resp.get("stat") != "Ok":
            return []

        return [
            {"symbol": s.get("tsym", ""), "token": s.get("token", ""), "name": s.get("cname", "")}
            for s in resp.get("values", [])
        ]

    def logout(self):
        """Logout from broker."""
        if self._api and self._logged_in:
            self._api.logout()
            self._logged_in = False
            self.logger.info("broker_logout")
