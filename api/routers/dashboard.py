"""Dashboard endpoints."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import get_config, get_db
from api.models.dashboard import DailyPnL, DashboardMetrics
from api.services.db import get_daily_pnl, get_dashboard_metrics

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardMetrics)
def dashboard(
    config: dict = Depends(get_config),
    conn: sqlite3.Connection = Depends(get_db),
):
    try:
        metrics = get_dashboard_metrics(conn, config)
        return DashboardMetrics(**metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/dashboard/daily-pnl", response_model=list[DailyPnL])
def daily_pnl(
    days: int = Query(default=30, ge=1, le=365),
    conn: sqlite3.Connection = Depends(get_db),
):
    try:
        rows = get_daily_pnl(conn, days)
        return [DailyPnL(**r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
