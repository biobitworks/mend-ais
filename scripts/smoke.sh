#!/usr/bin/env bash
set -euo pipefail
PORT="${MEND_PORT:-8899}"
BASE="http://127.0.0.1:$PORT"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

curl -fsS "$BASE/api/status" > "$TMP/status.json"
curl -fsS "$BASE/api/demo?purpose=research" > "$TMP/research.json"
curl -fsS "$BASE/api/fcg" > "$TMP/fcg.json"

python3 - "$TMP" <<'PY'
import json, pathlib, sys
root=pathlib.Path(sys.argv[1])
status=json.loads((root/"status.json").read_text())
demo=json.loads((root/"research.json").read_text())
fcg=json.loads((root/"fcg.json").read_text())
assert status["status"] == "PASS", status
assert status["services"]["ollama"]["status"] == "PASS", status
assert status["services"]["core_model"]["status"] == "PASS", status
assert demo["demo_state"] == "EXECUTED", demo
assert demo["egress_scan"]["pass"] is True, demo
assert demo["egress_scan"]["forbidden_hits"] == [], demo
ids={n["id"] for n in fcg["nodes"]}
for edge in fcg["edges"]:
    assert edge["from"] in ids and edge["to"] in ids, edge
print("PASS: server")
print("PASS: Ollama + core model present")
print("PASS: research release executed")
print("PASS: explicit-identifier egress scan zero hits")
print(f"MODEL_TRANSPORT={demo['model_advisory']['transport']}")
print(f"MODEL_STATUS={demo['model_advisory']['status']}")
print(f"DATASET_SHA256={demo['dataset']['sha256']}")
print(f"RELEASE_SHA256={demo['release_sha256']}")
PY
