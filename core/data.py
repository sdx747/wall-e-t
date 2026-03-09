"""Data manager for Wall-E-T.

Handles historical data fetching from yfinance/jugaad-data,
SQLite caching, and data retrieval for strategies and backtesting.
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

from core.logger import JsonLogger

# Default DB path relative to project root
_DEFAULT_DB = Path(__file__).parent.parent / "data" / "history.db"

# SQL for creating the OHLCV table
_CREATE_OHLCV = """
CREATE TABLE IF NOT EXISTS ohlcv (
    symbol      TEXT NOT NULL,
    exchange    TEXT NOT NULL,
    timeframe   TEXT NOT NULL,
    timestamp   TEXT NOT NULL,
    open        REAL,
    high        REAL,
    low         REAL,
    close       REAL,
    volume      INTEGER,
    PRIMARY KEY (symbol, exchange, timeframe, timestamp)
)
"""

_CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_ohlcv_lookup
ON ohlcv (symbol, exchange, timeframe, timestamp)
"""


class DataManager:
    """Fetches, caches, and serves market data."""

    def __init__(self, config: dict, logger: JsonLogger):
        self.logger = logger
        db_path = Path(config.get("db_path", str(_DEFAULT_DB)))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self.default_exchange = config.get("default_exchange", "NSE")
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(_CREATE_OHLCV)
            conn.execute(_CREATE_INDEX)

    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    @staticmethod
    def _to_yf_symbol(symbol: str, exchange: str) -> str:
        """Convert NSE/BSE symbol to yfinance format."""
        suffix = ".NS" if exchange.upper() == "NSE" else ".BO"
        # Don't double-add suffix
        if symbol.endswith(suffix):
            return symbol
        return f"{symbol}{suffix}"

    def fetch_historical(
        self,
        symbol: str,
        exchange: str | None = None,
        start: str | None = None,
        end: str | None = None,
        timeframe: str = "1d",
        force: bool = False,
    ) -> pd.DataFrame:
        """Fetch historical OHLCV data. Uses cache unless force=True.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE").
            exchange: "NSE" or "BSE". Defaults to config default.
            start: Start date as "YYYY-MM-DD". Defaults to 2 years ago.
            end: End date as "YYYY-MM-DD". Defaults to today.
            timeframe: Candle timeframe (e.g., "1d", "1wk").
            force: If True, skip cache and re-fetch from source.

        Returns:
            DataFrame with columns [open, high, low, close, volume], indexed by datetime.
        """
        exchange = exchange or self.default_exchange
        end = end or datetime.now().strftime("%Y-%m-%d")
        start = start or (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")

        # Try cache first
        if not force:
            cached = self._load_from_db(symbol, exchange, timeframe, start, end)
            if not cached.empty:
                self.logger.debug("data_cache_hit", symbol=symbol, rows=len(cached))
                return cached

        # Fetch from yfinance
        df = self._fetch_yfinance(symbol, exchange, start, end, timeframe)

        if df.empty:
            self.logger.warning("data_fetch_empty", symbol=symbol, source="yfinance")
            return df

        # Cache to SQLite
        self._save_to_db(df, symbol, exchange, timeframe)
        self.logger.info(
            "data_fetched", symbol=symbol, exchange=exchange, rows=len(df), source="yfinance"
        )
        return df

    def _fetch_yfinance(
        self, symbol: str, exchange: str, start: str, end: str, timeframe: str
    ) -> pd.DataFrame:
        """Download data from Yahoo Finance."""
        yf_symbol = self._to_yf_symbol(symbol, exchange)
        try:
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(start=start, end=end, interval=timeframe)
            if df.empty:
                return df

            # Normalize column names to lowercase
            df.columns = [c.lower().replace(" ", "_") for c in df.columns]
            # Keep only OHLCV columns
            keep = [c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]
            df = df[keep]
            # Ensure index is timezone-naive datetime
            df.index = pd.to_datetime(df.index).tz_localize(None)
            df.index.name = "timestamp"
            return df

        except Exception as e:
            self.logger.error("data_fetch_error", symbol=symbol, error=str(e))
            return pd.DataFrame()

    def _save_to_db(self, df: pd.DataFrame, symbol: str, exchange: str, timeframe: str):
        """Upsert OHLCV data into SQLite."""
        records = []
        for ts, row in df.iterrows():
            records.append((
                symbol, exchange, timeframe, ts.isoformat(),
                row.get("open"), row.get("high"), row.get("low"),
                row.get("close"), row.get("volume"),
            ))

        with self._get_conn() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO ohlcv
                (symbol, exchange, timeframe, timestamp, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                records,
            )

    def _load_from_db(
        self, symbol: str, exchange: str, timeframe: str, start: str, end: str
    ) -> pd.DataFrame:
        """Load cached OHLCV data from SQLite."""
        with self._get_conn() as conn:
            query = """
                SELECT timestamp, open, high, low, close, volume
                FROM ohlcv
                WHERE symbol = ? AND exchange = ? AND timeframe = ?
                  AND timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp
            """
            df = pd.read_sql_query(
                query, conn, params=(symbol, exchange, timeframe, start, end),
                parse_dates=["timestamp"], index_col="timestamp",
            )
        return df

    def get_candles(
        self,
        symbol: str,
        exchange: str | None = None,
        timeframe: str = "1d",
        n: int = 200,
    ) -> pd.DataFrame:
        """Get the latest N candles for a symbol from cache.

        Fetches from source if cache doesn't have enough data.
        """
        exchange = exchange or self.default_exchange
        end = datetime.now().strftime("%Y-%m-%d")
        # Estimate how far back to go (1.5x to account for weekends/holidays)
        days_back = int(n * 1.5) if timeframe == "1d" else n * 7
        start = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        df = self._load_from_db(symbol, exchange, timeframe, start, end)

        if len(df) < n:
            df = self.fetch_historical(symbol, exchange, start, end, timeframe, force=True)

        return df.tail(n)

    def fetch_multiple(
        self,
        symbols: list[str],
        exchange: str | None = None,
        start: str | None = None,
        end: str | None = None,
        timeframe: str = "1d",
    ) -> dict[str, pd.DataFrame]:
        """Fetch historical data for multiple symbols.

        Returns:
            Dict mapping symbol -> DataFrame.
        """
        results = {}
        for symbol in symbols:
            df = self.fetch_historical(symbol, exchange, start, end, timeframe)
            if not df.empty:
                results[symbol] = df
        return results

    def list_cached_symbols(self) -> list[dict]:
        """List all symbols in the database with their date ranges."""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT symbol, exchange, timeframe,
                       MIN(timestamp) as first_date,
                       MAX(timestamp) as last_date,
                       COUNT(*) as candles
                FROM ohlcv
                GROUP BY symbol, exchange, timeframe
                ORDER BY symbol
            """).fetchall()

        return [
            {
                "symbol": r[0], "exchange": r[1], "timeframe": r[2],
                "first_date": r[3], "last_date": r[4], "candles": r[5],
            }
            for r in rows
        ]
