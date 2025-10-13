#!/usr/bin/env bash
set -euo pipefail

# Simple setup script for a Python virtual environment and dependencies
# Works on Linux/macOS with Python 3.8-3.11

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python3 is required." >&2
  exit 1
fi

PY=$(command -v python3)
VENV_DIR=".venv"

$PY -m venv "$VENV_DIR"
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

pip install --upgrade pip wheel setuptools
pip install -r requirements.txt

echo "\n[OK] Virtualenv created in $VENV_DIR and dependencies installed."
echo "Activate with: source $VENV_DIR/bin/activate"