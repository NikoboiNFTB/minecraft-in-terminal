#!/bin/bash

set -e

cd "$(dirname "$0")"

if ! command -v wmctrl >/dev/null || ! command -v xwininfo >/dev/null; then
	echo "Missing system dependencies."
	echo "Install with: sudo apt install wmctrl x11-utils"
	exit 1
fi

if [ ! -d ".venv" ]; then
	echo "Creating virtual environment..."
	python3 -m venv .venv
	.venv/bin/python -m pip install -r requirements.txt
fi

exec .venv/bin/python main.py
