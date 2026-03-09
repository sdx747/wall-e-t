"""EMA Crossover strategy for Wall-E-T.

Generates BUY signals when a fast EMA crosses above a slow EMA,
and SELL signals on the reverse crossover. Uses a 200 EMA trend
filter to avoid trading against the primary trend.

Suitable for swing and positional trading on daily timeframes.
"""

import pandas as pd

from strategies.base import Signal, Side, SignalType, Strategy


class EMACrossover(Strategy):
    name = "ema_crossover"
    version = "1.0"
    style = "swing"
    timeframe = "1d"

    def configure(self, params: dict) -> None:
        self.fast_period = params.get("fast_period", 9)
        self.slow_period = params.get("slow_period", 21)
        self.trend_period = 200
        self.exchange = "NSE"
        self.product = params.get("product", "CNC")

        symbols = params.get("symbols", [])
        self._symbols = [(s, self.exchange) for s in symbols]

    def get_watchlist(self) -> list[tuple[str, str]]:
        return self._symbols

    def lookback(self) -> int:
        return self.trend_period + 10

    def on_candle(self, symbol: str, candles: pd.DataFrame) -> list[Signal]:
        if len(candles) < self.trend_period:
            return []

        # Compute EMAs using pandas built-in ewm
        close = candles["close"]
        fast_ema = close.ewm(span=self.fast_period, adjust=False).mean()
        slow_ema = close.ewm(span=self.slow_period, adjust=False).mean()
        trend_ema = close.ewm(span=self.trend_period, adjust=False).mean()

        # Current and previous values
        fast_now = fast_ema.iloc[-1]
        fast_prev = fast_ema.iloc[-2]
        slow_now = slow_ema.iloc[-1]
        slow_prev = slow_ema.iloc[-2]
        trend_now = trend_ema.iloc[-1]
        price = candles["close"].iloc[-1]

        signals = []

        # BUY: fast crosses above slow, price above trend EMA
        if fast_prev <= slow_prev and fast_now > slow_now and price > trend_now:
            signals.append(Signal(
                symbol=symbol,
                exchange=self.exchange,
                side=Side.BUY,
                signal_type=SignalType.ENTRY,
                product=self.product,
                stop_loss=slow_now * 0.98,  # 2% below slow EMA
                reason=(
                    f"EMA crossover BUY: EMA({self.fast_period})={fast_now:.2f} "
                    f"crossed above EMA({self.slow_period})={slow_now:.2f}, "
                    f"price={price:.2f} above EMA({self.trend_period})={trend_now:.2f}"
                ),
                metadata={
                    "fast_ema": round(fast_now, 2),
                    "slow_ema": round(slow_now, 2),
                    "trend_ema": round(trend_now, 2),
                },
            ))

        # SELL: fast crosses below slow
        elif fast_prev >= slow_prev and fast_now < slow_now:
            signals.append(Signal(
                symbol=symbol,
                exchange=self.exchange,
                side=Side.SELL,
                signal_type=SignalType.EXIT,
                product=self.product,
                reason=(
                    f"EMA crossover SELL: EMA({self.fast_period})={fast_now:.2f} "
                    f"crossed below EMA({self.slow_period})={slow_now:.2f}"
                ),
                metadata={
                    "fast_ema": round(fast_now, 2),
                    "slow_ema": round(slow_now, 2),
                },
            ))

        return signals
