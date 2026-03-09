"""FastAPI application for Wall-E-T dashboard."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.deps import get_config, get_data_manager, get_logger
from api.routers import backtest, config, dashboard, data, positions, strategies, trades


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: load config, initialize DataManager and logger."""
    logger = get_logger()
    logger.info("api_starting")
    # Eagerly initialize the data manager so it's cached
    get_data_manager()
    cfg = get_config()
    logger.info(
        "api_ready",
        mode=cfg.get("bot", {}).get("mode", "paper"),
        strategy=cfg.get("bot", {}).get("active_strategy", ""),
    )
    yield
    logger.info("api_shutdown")
    logger.close()


app = FastAPI(
    title="Wall-E-T API",
    description="Trading bot dashboard API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS - allow the Next.js frontend on localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(dashboard.router)
app.include_router(trades.router)
app.include_router(positions.router)
app.include_router(backtest.router)
app.include_router(strategies.router)
app.include_router(data.router)
app.include_router(config.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
