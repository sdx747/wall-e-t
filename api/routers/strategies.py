"""Strategy endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_config
from api.models.strategies import StrategyDetail, StrategyInfo
from core.config import get_strategy_config
from strategies import discover_strategies

router = APIRouter(prefix="/api", tags=["strategies"])


@router.get("/strategies", response_model=list[StrategyInfo])
def list_strategies(config: dict = Depends(get_config)):
    registry = discover_strategies()
    active = config.get("bot", {}).get("active_strategy", "")

    result = []
    for name, cls in registry.items():
        result.append(
            StrategyInfo(
                name=cls.name,
                version=cls.version,
                style=cls.style,
                timeframe=cls.timeframe,
                is_active=(cls.name == active),
            )
        )
    return result


@router.get("/strategies/{name}", response_model=StrategyDetail)
def get_strategy(name: str, config: dict = Depends(get_config)):
    registry = discover_strategies()
    if name not in registry:
        raise HTTPException(
            status_code=404,
            detail=f"Strategy '{name}' not found. Available: {list(registry.keys())}",
        )

    cls = registry[name]
    active = config.get("bot", {}).get("active_strategy", "")

    # Try to configure so we can get the watchlist
    instance = cls()
    try:
        params = get_strategy_config(config, name)
        instance.configure(params)
        watchlist = instance.get_watchlist()
        lookback = instance.lookback()
    except (ValueError, Exception):
        params = {}
        watchlist = []
        lookback = 200

    return StrategyDetail(
        name=cls.name,
        version=cls.version,
        style=cls.style,
        timeframe=cls.timeframe,
        is_active=(cls.name == active),
        watchlist=watchlist,
        lookback=lookback,
        config=params,
    )
