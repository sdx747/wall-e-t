"""Positions endpoints."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_db
from api.services.db import get_positions_from_orders

router = APIRouter(prefix="/api", tags=["positions"])


@router.get("/positions")
def list_positions(
    conn: sqlite3.Connection = Depends(get_db),
):
    try:
        positions = get_positions_from_orders(conn)
        return positions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
