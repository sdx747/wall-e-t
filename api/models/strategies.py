"""Strategy-related Pydantic models."""

from pydantic import BaseModel


class StrategyInfo(BaseModel):
    name: str
    version: str
    style: str
    timeframe: str
    is_active: bool = False


class StrategyDetail(StrategyInfo):
    watchlist: list[tuple[str, str]] = []
    lookback: int = 200
    config: dict = {}
