"""Data endpoints for OHLCV and cached symbols."""

from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import get_data_manager
from core.data import DataManager

router = APIRouter(prefix="/api", tags=["data"])


@router.get("/data/symbols")
def list_symbols(dm: DataManager = Depends(get_data_manager)):
    """List all cached symbols with their date ranges."""
    try:
        return dm.list_cached_symbols()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/ohlcv/{symbol}")
def get_ohlcv(
    symbol: str,
    exchange: str = Query(default="NSE"),
    start: str | None = Query(default=None, description="Start date YYYY-MM-DD"),
    end: str | None = Query(default=None, description="End date YYYY-MM-DD"),
    dm: DataManager = Depends(get_data_manager),
):
    """Get OHLCV candles for a symbol."""
    try:
        df = dm.fetch_historical(symbol, exchange, start, end)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if df.empty:
        return []

    candles = []
    for ts, row in df.iterrows():
        candles.append({
            "timestamp": ts.isoformat(),
            "open": round(row["open"], 2),
            "high": round(row["high"], 2),
            "low": round(row["low"], 2),
            "close": round(row["close"], 2),
            "volume": int(row["volume"]) if row["volume"] is not None else 0,
        })
    return candles
