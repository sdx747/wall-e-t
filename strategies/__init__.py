"""Strategy auto-discovery. Import all Strategy subclasses from this package."""

import importlib
import pkgutil
from pathlib import Path

from strategies.base import Strategy


def discover_strategies() -> dict[str, type[Strategy]]:
    """Scan the strategies package and return {name: StrategyClass} for all valid strategies."""
    registry: dict[str, type[Strategy]] = {}
    package_dir = Path(__file__).parent

    for module_info in pkgutil.iter_modules([str(package_dir)]):
        if module_info.name == "base":
            continue
        module = importlib.import_module(f"strategies.{module_info.name}")
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, Strategy)
                and attr is not Strategy
            ):
                registry[attr.name] = attr

    return registry
