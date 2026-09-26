#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ -f "$ROOT/.run/server.pid" ]; then
  PID="$(cat "$ROOT/.run/server.pid")"
  kill "$PID" 2>/dev/null || true
  rm -f "$ROOT/.run/server.pid"
  echo "Stopped Mend AIs demo PID $PID"
else
  echo "No recorded Mend AIs PID."
fi
