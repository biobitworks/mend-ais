#!/usr/bin/env bash
set -euo pipefail
PORT="${MEND_PORT:-8899}"
curl -fsS "http://127.0.0.1:$PORT/api/status"
echo
