"""Trade-related Pydantic models."""

from pydantic import BaseModel


class Trade(BaseModel):
    id: int
    symbol: str
    exchange: str
    side: str
    entry_price: float | None = None
    exit_price: float | None = None
    quantity: int | None = None
    pnl: float | None = None
    pnl_pct: float | None = None
    entry_time: str | None = None
    exit_time: str | None = None
    strategy: str | None = None
    mode: str = "paper"


class TradeListResponse(BaseModel):
    trades: list[Trade]
    total: int
