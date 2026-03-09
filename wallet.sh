#!/usr/bin/env bash
# Wall-E-T: Algo Trading Bot for Indian Markets
# Usage: ./wallet.sh <command> [args]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$HOME/.venvs/wall-e-t"
PYTHON="$VENV/bin/python"

# Check venv exists
if [ ! -f "$PYTHON" ]; then
    echo "Error: Virtual environment not found at $VENV"
    echo "Create it with: python3 -m venv $VENV"
    exit 1
fi

# Activate and run
cd "$SCRIPT_DIR"
exec "$PYTHON" cli.py "$@"
