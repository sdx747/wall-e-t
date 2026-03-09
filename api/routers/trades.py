"""Trades endpoints."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import get_db
from api.models.trades import Trade, TradeListResponse
from api.services.db import get_trades

router = APIRouter(prefix="/api", tags=["trades"])


@router.get("/trades", response_model=TradeListResponse)
def list_trades(
    symbol: str | None = Query(default=None),
    strategy: str | None = Query(default=None),
    start: str | None = Query(default=None, description="Start date YYYY-MM-DD"),
    end: str | None = Query(default=None, description="End date YYYY-MM-DD"),
    sort: str = Query(default="exit_time"),
    order: str = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=500),
    conn: sqlite3.Connection = Depends(get_db),
):
    try:
        rows, total = get_trades(
            conn,
            symbol=symbol,
            strategy=strategy,
            start=start,
            end=end,
            sort=sort,
            order=order,
            page=page,
            per_page=per_page,
        )
        trades = [Trade(**r) for r in rows]
        return TradeListResponse(trades=trades, total=total)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
