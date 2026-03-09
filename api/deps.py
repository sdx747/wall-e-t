"""FastAPI dependency injection providers."""

import sqlite3
from functools import lru_cache
from pathlib import Path

from core.config import load_config
from core.data import DataManager
from core.logger import JsonLogger

_PROJECT_ROOT = Path(__file__).parent.parent
_DB_PATH = _PROJECT_ROOT / "data" / "history.db"


@lru_cache
def get_config() -> dict:
    """Return the loaded config dict (cached)."""
    return load_config()


@lru_cache
def get_logger() -> JsonLogger:
    """Return a JsonLogger instance (cached)."""
    config = get_config()
    level = config.get("bot", {}).get("log_level", "info")
    return JsonLogger(log_level=level)


def get_db() -> sqlite3.Connection:
    """Return a read-only SQLite connection to history.db."""
    db_uri = f"file:{_DB_PATH}?mode=ro"
    conn = sqlite3.connect(db_uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


@lru_cache
def get_data_manager() -> DataManager:
    """Return a DataManager instance (cached)."""
    config = get_config()
    logger = get_logger()
    data_config = config.get("data", {})
    # Resolve db_path relative to project root
    db_path = data_config.get("db_path", str(_DB_PATH))
    if not Path(db_path).is_absolute():
        db_path = str(_PROJECT_ROOT / db_path)
    data_config["db_path"] = db_path
    return DataManager(data_config, logger)
