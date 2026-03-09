"""Telegram notification for Wall-E-T.

Sends trade alerts, daily P&L summaries, and error notifications
via the Telegram Bot API. Uses plain HTTP requests — no framework needed.
"""

import json
from urllib.request import Request, urlopen
from urllib.error import URLError

from core.logger import JsonLogger

_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


class Notifier:
    """Sends notifications via Telegram Bot API."""

    def __init__(self, config: dict, logger: JsonLogger):
        self.logger = logger
        self.token = config.get("bot_token", "")
        self.chat_id = config.get("chat_id", "")
        self.enabled = config.get("enabled", False)
        self.on_trade = config.get("on_trade", True)
        self.on_error = config.get("on_error", True)
        self.daily_report = config.get("daily_report", True)

    def _send(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Send a message via Telegram Bot API."""
        if not self.enabled or not self.token or not self.chat_id:
            return False

        url = _API_URL.format(token=self.token)
        payload = json.dumps({
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }).encode()

        req = Request(url, data=payload, headers={"Content-Type": "application/json"})

        try:
            with urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except (URLError, OSError) as e:
            self.logger.error("notification_failed", error=str(e))
            return False

    def trade_alert(self, symbol: str, side: str, qty: int, price: float, reason: str = ""):
        """Send a trade execution alert."""
        if not self.on_trade:
            return

        emoji = "🟢" if side == "BUY" else "🔴"
        msg = (
            f"{emoji} *{side}* {symbol}\n"
            f"Qty: {qty} @ ₹{price:,.2f}\n"
        )
        if reason:
            msg += f"Reason: {reason}\n"

        self._send(msg)

    def trade_closed(self, symbol: str, entry: float, exit_price: float, qty: int, pnl: float):
        """Send a trade closure notification."""
        if not self.on_trade:
            return

        emoji = "✅" if pnl > 0 else "❌"
        pnl_pct = ((exit_price / entry) - 1) * 100
        msg = (
            f"{emoji} *Closed* {symbol}\n"
            f"Entry: ₹{entry:,.2f} → Exit: ₹{exit_price:,.2f}\n"
            f"Qty: {qty} | P&L: ₹{pnl:+,.2f} ({pnl_pct:+.2f}%)\n"
        )
        self._send(msg)

    def daily_summary(self, stats: dict):
        """Send end-of-day P&L summary."""
        if not self.daily_report:
            return

        pnl = stats.get("daily_pnl", 0)
        emoji = "📈" if pnl >= 0 else "📉"
        msg = (
            f"{emoji} *Daily Summary*\n"
            f"P&L: ₹{pnl:+,.2f}\n"
            f"Open positions: {stats.get('open_positions', 0)}\n"
            f"Trades today: {stats.get('trades_today', 0)}\n"
        )
        self._send(msg)

    def error(self, error: str):
        """Send an error alert."""
        if not self.on_error:
            return
        self._send(f"⚠️ *Error*\n{error}")

    def send(self, text: str):
        """Send a raw text message."""
        self._send(text)
