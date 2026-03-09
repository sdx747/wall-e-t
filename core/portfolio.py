"""Portfolio tracker for Wall-E-T.

Tracks open positions, completed trades, and P&L.
Persists trades to SQLite for analysis.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

from core.logger import JsonLogger

_CREATE_ORDERS = """
CREATE TABLE IF NOT EXISTS orders (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id    TEXT NOT NULL,
    timestamp   TEXT NOT NULL,
    symbol      TEXT NOT NULL,
    exchange    TEXT NOT NULL,
    side        TEXT NOT NULL,
    quantity    INTEGER,
    price       REAL,
    trigger_price REAL,
    order_type  TEXT,
    product     TEXT,
    status      TEXT,
    fill_price  REAL,
    fill_time   TEXT,
    strategy    TEXT,
    signal_reason TEXT,
    mode        TEXT DEFAULT 'paper'
)
"""

_CREATE_TRADES = """
CREATE TABLE IF NOT EXISTS trades (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol          TEXT NOT NULL,
    exchange        TEXT NOT NULL,
    side            TEXT NOT NULL,
    entry_price     REAL,
    exit_price      REAL,
    quantity        INTEGER,
    pnl             REAL,
    pnl_pct         REAL,
    entry_time      TEXT,
    exit_time       TEXT,
    strategy        TEXT,
    mode            TEXT DEFAULT 'paper'
)
"""


class PortfolioTracker:
    """Tracks positions, records trades to DB."""

    def __init__(self, db_path: str | Path, logger: JsonLogger, mode: str = "paper"):
        self.logger = logger
        self.mode = mode
        self.db_path = Path(db_path)
        self._init_db()

        # Active positions: symbol -> {qty, avg_price, entry_time, strategy}
        self.positions: dict[str, dict] = {}

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(_CREATE_ORDERS)
            conn.execute(_CREATE_TRADES)

    def record_order(self, order: dict, strategy: str, reason: str):
        """Record an order to the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO orders
                (order_id, timestamp, symbol, exchange, side, quantity, price,
                 trigger_price, order_type, product, status, fill_price, fill_time,
                 strategy, signal_reason, mode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    order.get("order_id"), order.get("placed_at", datetime.now().isoformat()),
                    order.get("symbol"), order.get("exchange"), order.get("side"),
                    order.get("qty"), order.get("price"), order.get("trigger_price"),
                    order.get("order_type"), order.get("product"), order.get("status"),
                    order.get("fill_price"), order.get("fill_time"),
                    strategy, reason, self.mode,
                ),
            )

    def open_position(self, symbol: str, exchange: str, qty: int, price: float, strategy: str):
        """Track a new position entry."""
        self.positions[symbol] = {
            "qty": qty,
            "avg_price": price,
            "exchange": exchange,
            "entry_time": datetime.now().isoformat(),
            "strategy": strategy,
        }

    def close_position(self, symbol: str, exit_price: float) -> float:
        """Close a position and record the trade. Returns P&L."""
        if symbol not in self.positions:
            return 0.0

        pos = self.positions.pop(symbol)
        pnl = (exit_price - pos["avg_price"]) * pos["qty"]
        pnl_pct = ((exit_price / pos["avg_price"]) - 1) * 100

        # Record to DB
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO trades
                (symbol, exchange, side, entry_price, exit_price, quantity,
                 pnl, pnl_pct, entry_time, exit_time, strategy, mode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    symbol, pos["exchange"], "LONG", pos["avg_price"], exit_price,
                    pos["qty"], round(pnl, 2), round(pnl_pct, 2),
                    pos["entry_time"], datetime.now().isoformat(),
                    pos["strategy"], self.mode,
                ),
            )

        self.logger.info(
            "trade_closed",
            symbol=symbol,
            entry=round(pos["avg_price"], 2),
            exit=round(exit_price, 2),
            qty=pos["qty"],
            pnl=round(pnl, 2),
            pnl_pct=round(pnl_pct, 2),
        )
        return pnl

    def has_position(self, symbol: str) -> bool:
        return symbol in self.positions

    def get_positions(self) -> list[dict]:
        return [
            {"symbol": sym, **pos}
            for sym, pos in self.positions.items()
        ]

    def get_today_trades(self) -> list[dict]:
        """Get all trades from today."""
        today = datetime.now().strftime("%Y-%m-%d")
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM trades WHERE exit_time LIKE ? AND mode = ?",
                (f"{today}%", self.mode),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_today_pnl(self) -> float:
        """Get total P&L for today."""
        trades = self.get_today_trades()
        return sum(t["pnl"] for t in trades)
