#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "breakpoints/mend_core_breakpoint_v1.json"

def h(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()

m = json.loads(MANIFEST.read_text())
level = []
errors = []
for leaf in m["canonical_leaves"]:
    path = ROOT / leaf["path"]
    if not path.is_file():
        errors.append(f"missing file: {leaf['path']}")
        continue
    raw = path.read_bytes()
    file_hash = hashlib.sha256(raw).hexdigest()
    if file_hash != leaf["file_sha256"]:
        errors.append(f"file hash mismatch: {leaf['path']}")
        continue
    preimage = b"mend-core-leaf-v1\0" + leaf["path"].encode() + b"\0" + file_hash.encode()
    leaf_hash = h(preimage).hex()
    if leaf_hash != leaf["leaf_sha256"]:
        errors.append(f"leaf hash mismatch: {leaf['path']}")
    level.append(bytes.fromhex(leaf_hash))

if errors:
    for e in errors:
        print("FAIL:", e)
    sys.exit(1)

while len(level) > 1:
    if len(level) % 2:
        level = level + [level[-1]]
    level = [
        h(b"mend-core-node-v1\0" + level[i] + level[i + 1])
        for i in range(0, len(level), 2)
    ]

actual = level[0].hex()
if actual != m["merkle_root_sha256"]:
    print("FAIL: merkle root mismatch")
    sys.exit(2)

print("PASS")
print("BREAKPOINT_ID=" + m["breakpoint_id"])
print("MERKLE_ROOT_SHA256=" + actual)
print("CANONICAL_LEAF_COUNT=" + str(m["canonical_leaf_count"]))
