#!/bin/zsh
set -e
cd "$(dirname "$0")"
echo "Starting Forsyth Connect at http://127.0.0.1:8000"
python3 backend/server.py --host 127.0.0.1 --port 8000 --workers 128
