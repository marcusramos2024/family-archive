#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# One-time venv + install.
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  ./.venv/bin/pip install --upgrade pip
  ./.venv/bin/pip install -r requirements.txt
fi

./.venv/bin/python pipeline.py
