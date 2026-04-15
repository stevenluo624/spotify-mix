#!/usr/bin/env bash
# Convenience wrapper: activates the virtual environment (if present) and runs the tool.
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ -d ".venv" ]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
fi

python main.py "$@"
