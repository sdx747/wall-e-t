"""Structured JSONL logger for Wall-E-T.

Writes one JSON object per line to daily log files in data/logs/.
Every event includes timestamp, event type, and contextual data.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent / "data" / "logs"


class JsonLogger:
    """Writes structured JSONL logs and also logs to console."""

    def __init__(self, log_level: str = "info"):
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        self._log_level = getattr(logging, log_level.upper(), logging.INFO)

        # Console logger
        self._console = logging.getLogger("wall-e-t")
        self._console.setLevel(self._log_level)
        if not self._console.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
            )
            self._console.addHandler(handler)

        self._current_date: str | None = None
        self._file = None

    def _get_file(self):
        """Get or rotate the log file based on current date."""
        today = datetime.now().strftime("%Y-%m-%d")
        if self._current_date != today:
            if self._file:
                self._file.close()
            log_path = LOG_DIR / f"{today}.jsonl"
            self._file = open(log_path, "a")
            self._current_date = today
        return self._file

    def log(self, event: str, level: str = "info", **data):
        """Log a structured event.

        Args:
            event: Event type (e.g., "signal_generated", "order_placed").
            level: Log level ("debug", "info", "warning", "error").
            **data: Arbitrary key-value data to include.
        """
        log_level = getattr(logging, level.upper(), logging.INFO)
        if log_level < self._log_level:
            return

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "level": level,
            **data,
        }

        # Write to JSONL file
        f = self._get_file()
        f.write(json.dumps(record, default=str) + "\n")
        f.flush()

        # Console output
        msg = f"[{event}] {json.dumps(data, default=str)}" if data else f"[{event}]"
        self._console.log(log_level, msg)

    def info(self, event: str, **data):
        self.log(event, level="info", **data)

    def debug(self, event: str, **data):
        self.log(event, level="debug", **data)

    def warning(self, event: str, **data):
        self.log(event, level="warning", **data)

    def error(self, event: str, **data):
        self.log(event, level="error", **data)

    def close(self):
        if self._file:
            self._file.close()
            self._file = None
