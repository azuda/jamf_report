#!/bin/sh

# resolve the project from this script's own location, not the caller's cwd
PROJECT="$(cd "$(dirname "$0")" && pwd)"
VENV="$PROJECT/.venv/bin/python3"

cd "$PROJECT" && exec "$VENV" main.py
