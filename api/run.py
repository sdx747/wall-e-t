"""Uvicorn entrypoint for the Wall-E-T API."""

import sys
from pathlib import Path

# Add project root to sys.path so `from core...` and `from strategies...` work
_PROJECT_ROOT = str(Path(__file__).parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import uvicorn


def main():
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[_PROJECT_ROOT],
    )


if __name__ == "__main__":
    main()
