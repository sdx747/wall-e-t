"""Config endpoint (safe subset only)."""

from fastapi import APIRouter, Depends

from api.deps import get_config

router = APIRouter(prefix="/api", tags=["config"])

# Sections to exclude from the API response (contain secrets)
_EXCLUDED_SECTIONS = {"broker", "telegram"}


@router.get("/config")
def read_config(config: dict = Depends(get_config)):
    """Return config with sensitive sections removed."""
    return {k: v for k, v in config.items() if k not in _EXCLUDED_SECTIONS}
