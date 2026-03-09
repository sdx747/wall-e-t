# Wall-E-T 🤖💰

An algorithmic trading bot for the Indian stock market (NSE/BSE). Built to be strategy-agnostic — swap trading strategies like batteries, without touching core code.

> **Wall-E-T** = Wall Street + Wall-E + Wallet. An alien robot that trades.

## Features

- **Plug-and-play strategies** — Drop a Python file in `strategies/`, it's auto-discovered
- **Backtesting engine** — Test any strategy against historical data before risking real money
- **Data pipeline** — Fetches and caches OHLCV data from Yahoo Finance with SQLite storage
- **Paper trading** — Simulate trades without real money (Phase 2)
- **Risk management** — Position sizing, stop-losses, daily loss limits (Phase 2)
- **Telegram alerts** — Get notified on trades and daily P&L (Phase 3)
- **CLI interface** — Simple commands for everything

## Current Status

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Data pipeline, strategy framework, backtesting | ✅ Complete |
| Phase 2 | Paper trading, risk manager, execution engine | 🔜 Planned |
| Phase 3 | Live trading (Shoonya broker), Telegram alerts | 🔜 Planned |
| Phase 4 | More strategies, deployment, monitoring | 🔜 Planned |

## Quick Start

### Prerequisites

- Python 3.14+
- Virtual environment at `~/.venvs/wall-e-t/`

### Setup

```bash
# Clone the repo
git clone https://github.com/<your-username>/wall-e-t.git
cd wall-e-t

# Create venv and install dependencies
python3 -m venv ~/.venvs/wall-e-t
~/.venvs/wall-e-t/bin/pip install -r requirements.txt

# Create your config
cp config.toml.example config.toml
# Edit config.toml with your settings

# Make the launcher executable
chmod +x wallet.sh
```

### Usage

```bash
# Show bot status
./wallet.sh status

# List available strategies
./wallet.sh strategy list

# Show strategy details
./wallet.sh strategy info ema_crossover

# Fetch historical data
./wallet.sh data fetch RELIANCE --start 2024-01-01
./wallet.sh data fetch INFY --start 2023-01-01

# List cached data
./wallet.sh data list

# Run a backtest
./wallet.sh backtest ema_crossover --start 2024-01-01

# Run backtest with individual trade details
./wallet.sh backtest ema_crossover --start 2024-01-01 -v

# View logs
./wallet.sh logs
./wallet.sh logs --date 2026-03-09
```

## Project Structure

```
wall-e-t/
├── wallet.sh                   # Shell launcher
├── cli.py                      # CLI entry point
├── config.toml.example         # Config template
├── requirements.txt
│
├── core/
│   ├── config.py               # TOML config loader with env var overrides
│   ├── data.py                 # Data fetching, caching, and retrieval
│   └── logger.py               # Structured JSONL audit logger
│
├── strategies/
│   ├── __init__.py             # Auto-discovers strategy files
│   ├── base.py                 # Strategy ABC — the plug-and-play interface
│   └── ema_crossover.py        # EMA crossover strategy (swing trading)
│
├── backtest/
│   └── runner.py               # Backtest engine with performance metrics
│
├── data/
│   ├── history.db              # SQLite cache (gitignored)
│   └── logs/                   # JSONL log files (gitignored)
│
└── tests/
```

## Creating a New Strategy

1. Create a file in `strategies/` (e.g., `strategies/my_strategy.py`)
2. Subclass `Strategy` from `strategies.base`
3. Implement three methods: `configure()`, `on_candle()`, `get_watchlist()`
4. Add a `[strategy.my_strategy]` section to `config.toml`
5. Done — it's auto-discovered

```python
from strategies.base import Strategy, Signal, Side, SignalType

class MyStrategy(Strategy):
    name = "my_strategy"
    version = "1.0"
    style = "swing"         # "intraday", "swing", or "positional"
    timeframe = "1d"

    def configure(self, params: dict) -> None:
        """Read strategy-specific params from config.toml."""
        self.period = params.get("period", 14)
        symbols = params.get("symbols", [])
        self._symbols = [(s, "NSE") for s in symbols]

    def on_candle(self, symbol: str, candles) -> list[Signal]:
        """Called on every new candle. Return signals or empty list."""
        # Your logic here — compute indicators, detect patterns
        price = candles["close"].iloc[-1]

        if your_buy_condition:
            return [Signal(
                symbol=symbol,
                exchange="NSE",
                side=Side.BUY,
                signal_type=SignalType.ENTRY,
                stop_loss=price * 0.95,
                reason="Why this trade makes sense",
            )]
        return []

    def get_watchlist(self) -> list[tuple[str, str]]:
        return self._symbols
```

## Configuration

All settings live in `config.toml`. Secrets can be overridden via environment variables:

```bash
export WALLET_BROKER_PASSWORD="your_password"
export WALLET_BROKER_API_SECRET="your_secret"
export WALLET_TELEGRAM_BOT_TOKEN="your_token"
```

See `config.toml.example` for all available options.

## Architecture

```
Data Sources ──→ DataManager ──→ Strategy.on_candle() ──→ Signals
(yfinance)       (SQLite cache)  (your logic)             │
                                                          ▼
                                                     RiskManager (Phase 2)
                                                          │
                                                          ▼
                                                     OrderExecutor (Phase 2)
                                                          │
                                                     ┌────┴────┐
                                                     ▼         ▼
                                                  Shoonya   Paper
                                                  Broker    Broker
```

Key design principle: **Strategies return Signal objects, never talk to the broker.** This separation enables paper trading, risk management, backtesting, and full audit logging — all transparently.

## Backtest Metrics

The backtester reports:
- **Total Return / CAGR** — Overall and annualized returns
- **Max Drawdown** — Worst peak-to-trough decline
- **Sharpe Ratio** — Risk-adjusted return (annualized)
- **Profit Factor** — Gross profit / gross loss
- **Win Rate** — Percentage of profitable trades
- **Avg Win / Avg Loss** — Average profit and loss per trade

## Tech Stack

| Component | Tool | Cost |
|-----------|------|------|
| Language | Python 3.14 | Free |
| Data | yfinance, jugaad-data | Free |
| Storage | SQLite | Free |
| Broker (Phase 3) | Shoonya (Finvasia) | Free API, zero brokerage |
| Notifications (Phase 3) | Telegram Bot | Free |
| Deployment (Phase 4) | Oracle Cloud Free Tier | Free |

## Disclaimer

This software is for educational and research purposes. Algorithmic trading involves financial risk. Past backtest performance does not guarantee future results. Always paper trade extensively before using real money. The authors are not responsible for any financial losses.

## License

MIT
