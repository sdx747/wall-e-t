"""Database query helpers for the API layer.

All functions take a sqlite3 connection and return plain dicts/lists.
"""

import sqlite3
from datetime import datetime, timedelta


def get_dashboard_metrics(conn: sqlite3.Connection, config: dict) -> dict:
    """Compute dashboard metrics from the trades and orders tables."""
    conn.row_factory = sqlite3.Row
    today = datetime.now().strftime("%Y-%m-%d")

    # Total P&L
    row = conn.execute("SELECT COALESCE(SUM(pnl), 0) AS total FROM trades").fetchone()
    total_pnl = row["total"]

    # Today's P&L
    row = conn.execute(
        "SELECT COALESCE(SUM(pnl), 0) AS today FROM trades WHERE exit_time LIKE ?",
        (f"{today}%",),
    ).fetchone()
    today_pnl = row["today"]

    # Open positions: BUY orders without a matching SELL (rough heuristic from orders table)
    open_count = _count_open_positions(conn)

    # Trade stats
    row = conn.execute("SELECT COUNT(*) AS cnt FROM trades").fetchone()
    total_trades = row["cnt"]

    if total_trades > 0:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM trades WHERE pnl > 0"
        ).fetchone()
        winning = row["cnt"]
        win_rate = round((winning / total_trades) * 100, 1)

        row = conn.execute(
            "SELECT COALESCE(SUM(pnl), 0) AS gp FROM trades WHERE pnl > 0"
        ).fetchone()
        gross_profit = row["gp"]

        row = conn.execute(
            "SELECT COALESCE(ABS(SUM(pnl)), 0) AS gl FROM trades WHERE pnl <= 0"
        ).fetchone()
        gross_loss = row["gl"]

        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else 0.0
    else:
        win_rate = 0.0
        profit_factor = 0.0

    # Max drawdown from cumulative P&L
    max_drawdown_pct = _compute_max_drawdown(conn, config)

    capital = config.get("risk", {}).get("capital", 0)
    mode = config.get("bot", {}).get("mode", "paper")
    active_strategy = config.get("bot", {}).get("active_strategy", "")

    return {
        "total_pnl": round(total_pnl, 2),
        "today_pnl": round(today_pnl, 2),
        "open_positions_count": open_count,
        "total_trades": total_trades,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "max_drawdown_pct": max_drawdown_pct,
        "capital": capital,
        "mode": mode,
        "active_strategy": active_strategy,
        "trading_halted": False,
    }


def _count_open_positions(conn: sqlite3.Connection) -> int:
    """Count open positions by finding BUY orders whose symbols have no later SELL."""
    try:
        rows = conn.execute("""
            SELECT DISTINCT o1.symbol
            FROM orders o1
            WHERE o1.side = 'BUY'
              AND o1.status IN ('complete', 'COMPLETE', 'filled', 'FILLED')
              AND NOT EXISTS (
                  SELECT 1 FROM orders o2
                  WHERE o2.symbol = o1.symbol
                    AND o2.side = 'SELL'
                    AND o2.status IN ('complete', 'COMPLETE', 'filled', 'FILLED')
                    AND o2.timestamp >= o1.timestamp
              )
        """).fetchall()
        return len(rows)
    except sqlite3.OperationalError:
        return 0


def _compute_max_drawdown(conn: sqlite3.Connection, config: dict) -> float:
    """Compute max drawdown percentage from trade history."""
    capital = config.get("risk", {}).get("capital", 100_000)

    rows = conn.execute(
        "SELECT pnl FROM trades ORDER BY exit_time"
    ).fetchall()

    if not rows:
        return 0.0

    cumulative = capital
    peak = capital
    max_dd = 0.0

    for row in rows:
        cumulative += row["pnl"]
        if cumulative > peak:
            peak = cumulative
        dd = (peak - cumulative) / peak * 100
        if dd > max_dd:
            max_dd = dd

    return round(max_dd, 2)


def get_daily_pnl(conn: sqlite3.Connection, days: int = 30) -> list[dict]:
    """Get daily P&L for the last N days."""
    conn.row_factory = sqlite3.Row
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    rows = conn.execute(
        """
        SELECT DATE(exit_time) AS date, SUM(pnl) AS pnl
        FROM trades
        WHERE exit_time >= ?
        GROUP BY DATE(exit_time)
        ORDER BY date
        """,
        (cutoff,),
    ).fetchall()

    result = []
    cumulative = 0.0
    for row in rows:
        cumulative += row["pnl"]
        result.append({
            "date": row["date"],
            "pnl": round(row["pnl"], 2),
            "cumulative_pnl": round(cumulative, 2),
        })

    return result


def get_trades(
    conn: sqlite3.Connection,
    symbol: str | None = None,
    strategy: str | None = None,
    start: str | None = None,
    end: str | None = None,
    sort: str = "exit_time",
    order: str = "desc",
    page: int = 1,
    per_page: int = 50,
) -> tuple[list[dict], int]:
    """Query trades with filtering, sorting, and pagination."""
    conn.row_factory = sqlite3.Row

    # Whitelist sort columns to prevent SQL injection
    allowed_sort = {"id", "symbol", "pnl", "pnl_pct", "entry_time", "exit_time", "strategy"}
    if sort not in allowed_sort:
        sort = "exit_time"
    if order.lower() not in ("asc", "desc"):
        order = "desc"

    conditions = []
    params: list = []

    if symbol:
        conditions.append("symbol = ?")
        params.append(symbol)
    if strategy:
        conditions.append("strategy = ?")
        params.append(strategy)
    if start:
        conditions.append("exit_time >= ?")
        params.append(start)
    if end:
        conditions.append("exit_time <= ?")
        params.append(end)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    # Count total
    count_row = conn.execute(
        f"SELECT COUNT(*) AS cnt FROM trades {where_clause}", params
    ).fetchone()
    total = count_row["cnt"]

    # Fetch page
    offset = (page - 1) * per_page
    rows = conn.execute(
        f"SELECT * FROM trades {where_clause} ORDER BY {sort} {order} LIMIT ? OFFSET ?",
        params + [per_page, offset],
    ).fetchall()

    return [dict(r) for r in rows], total


def get_positions_from_orders(conn: sqlite3.Connection) -> list[dict]:
    """Derive open positions from the orders table.

    Finds BUY orders whose symbols have no subsequent completed SELL order.
    """
    conn.row_factory = sqlite3.Row

    try:
        rows = conn.execute("""
            SELECT o1.symbol, o1.exchange, o1.quantity, o1.fill_price, o1.fill_time,
                   o1.strategy, o1.mode
            FROM orders o1
            WHERE o1.side = 'BUY'
              AND o1.status IN ('complete', 'COMPLETE', 'filled', 'FILLED')
              AND NOT EXISTS (
                  SELECT 1 FROM orders o2
                  WHERE o2.symbol = o1.symbol
                    AND o2.side = 'SELL'
                    AND o2.status IN ('complete', 'COMPLETE', 'filled', 'FILLED')
                    AND o2.timestamp >= o1.timestamp
              )
            ORDER BY o1.timestamp DESC
        """).fetchall()
    except sqlite3.OperationalError:
        return []

    return [
        {
            "symbol": r["symbol"],
            "exchange": r["exchange"],
            "quantity": r["quantity"],
            "entry_price": r["fill_price"],
            "entry_time": r["fill_time"],
            "strategy": r["strategy"],
            "mode": r["mode"],
        }
        for r in rows
    ]
