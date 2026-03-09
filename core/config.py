"""Configuration loader for Wall-E-T.

Reads config.toml and supports environment variable overrides for secrets.
Env vars follow the pattern: WALLET_<SECTION>_<KEY> (e.g., WALLET_BROKER_PASSWORD).
"""

import os
import tomllib
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config.toml"

# Keys that can be overridden via environment variables
_ENV_OVERRIDES = {
    "broker": ["user_id", "password", "vendor_code", "api_secret", "totp_secret"],
    "telegram": ["bot_token", "chat_id"],
}


def load_config(path: Path | None = None) -> dict:
    """Load configuration from TOML file with env var overrides for secrets."""
    config_file = path or CONFIG_PATH

    if not config_file.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_file}\n"
            f"Copy config.toml.example to config.toml and fill in your values."
        )

    with open(config_file, "rb") as f:
        config = tomllib.load(f)

    # Apply environment variable overrides
    for section, keys in _ENV_OVERRIDES.items():
        if section not in config:
            continue
        for key in keys:
            env_key = f"WALLET_{section.upper()}_{key.upper()}"
            env_val = os.environ.get(env_key)
            if env_val is not None:
                config[section][key] = env_val

    return config


def get_strategy_config(config: dict, strategy_name: str) -> dict:
    """Get strategy-specific parameters from config."""
    strategies = config.get("strategy", {})
    if strategy_name not in strategies:
        raise ValueError(
            f"No configuration found for strategy '{strategy_name}'. "
            f"Add a [strategy.{strategy_name}] section to config.toml."
        )
    return strategies[strategy_name]
