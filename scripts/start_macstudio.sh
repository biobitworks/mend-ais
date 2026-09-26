#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${MEND_PORT:-8899}"
MODEL="longhorizon-liquid-230m:latest"
mkdir -p "$ROOT/.run"

command -v python3 >/dev/null
command -v curl >/dev/null

if ! curl -fsS --max-time 3 http://127.0.0.1:11434/api/tags >/dev/null; then
  echo "FAIL: Ollama is not reachable on 127.0.0.1:11434" >&2
  exit 2
fi
if ! curl -fsS http://127.0.0.1:11434/api/tags | grep -q "$MODEL"; then
  echo "FAIL: required model $MODEL is not installed" >&2
  exit 3
fi

if curl -fsS --max-time 2 "http://127.0.0.1:$PORT/api/status" >/dev/null 2>&1; then
  echo "Mend AIs already running on port $PORT"
else
  nohup python3 "$ROOT/server.py" --host 0.0.0.0 --port "$PORT" >"$ROOT/.run/server.log" 2>&1 &
  echo $! > "$ROOT/.run/server.pid"
  for _ in {1..30}; do
    curl -fsS --max-time 1 "http://127.0.0.1:$PORT/api/status" >/dev/null 2>&1 && break
    sleep 0.2
  done
fi

LAN_IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)"
echo "LOCAL  http://127.0.0.1:$PORT"
[ -n "$LAN_IP" ] && echo "LAN    http://$LAN_IP:$PORT"
echo "MODEL  $MODEL"
echo "NEXT   ./scripts/smoke.sh"
