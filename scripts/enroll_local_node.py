#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
import os
import secrets
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BREAKPOINT = ROOT / "breakpoints/mend_core_breakpoint_v1.json"
CONFIG_DIR = Path.home() / ".config" / "mend-ais"
DESCRIPTOR = CONFIG_DIR / "unlock.json"

def existing_dir(path: Path):
    return str(path) if path.is_dir() else None

bp = json.loads(BREAKPOINT.read_text())
node_seed = secrets.token_bytes(32)
node_id = hashlib.sha256(b"mend-local-node-v1\0" + node_seed).hexdigest()

capabilities = {
    "runtime.model.local": {
        "url": os.environ.get("MEND_OLLAMA_URL", "http://127.0.0.1:11434"),
        "state": "LOCAL_DISCOVERY_REQUIRED",
    },
    "runtime.orchestrator.local": {
        "url": os.environ.get("MEND_OLLARMA_URL", "http://127.0.0.1:8484"),
        "state": "LOCAL_DISCOVERY_REQUIRED",
    },
    "framework.antigence.local": {
        "path": existing_dir(Path.home() / "projects" / "active" / "antigence"),
    },
    "framework.seedgraph.local": {
        "path": existing_dir(Path.home() / "projects" / "active" / "seedgraph"),
    },
    "framework.gsigmad.local": {
        "path": existing_dir(Path.home() / "projects" / "active" / "gettingsciencedone"),
    },
    "framework.ollarma.local": {
        "path": existing_dir(Path.home() / "projects" / "active" / "ollarma"),
    },
}

descriptor = {
    "schema_version": "mend.local_capability_descriptor.v1",
    "node_id": node_id,
    "breakpoint_root_sha256": bp["merkle_root_sha256"],
    "capabilities": capabilities,
    "note": "LOCAL PRIVATE DESCRIPTOR. Do not commit, publish, or copy into model prompts.",
}
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
DESCRIPTOR.write_text(json.dumps(descriptor, indent=2) + "\n")
os.chmod(DESCRIPTOR, stat.S_IRUSR | stat.S_IWUSR)
print("ENROLLED")
print("NODE_ID_SHA256=" + node_id)
print("BREAKPOINT_ROOT_SHA256=" + bp["merkle_root_sha256"])
print("CAPABILITY_COUNT=" + str(len(capabilities)))
