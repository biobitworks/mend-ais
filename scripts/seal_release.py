#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "receipts/public_release_receipt.json"
FILES = [
    ".gitignore",
    "README.md",
    "data/core/synthetic_fhir_bundle.json",
    "docs/ARCHITECTURE.md",
    "docs/JUDGE_NAVIGATION.md",
    "fcg/core_fcg.json",
    "receipts/demo_research_20260926.json",
    "receipts/studio_resource_audit_20260926.json",
    "sdk/js/mend-sdk.js",
    "sdk/python/mend_sdk.py",
    "server.py",
    "scripts/seal_release.py",
    "scripts/smoke.sh",
    "scripts/start_macstudio.sh",
    "scripts/status.sh",
    "scripts/stop.sh",
    "scripts/verify_fcg.py",
    "web/index.html",
]

def h(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()

leaves = []
for relative in sorted(FILES):
    path = ROOT / relative
    raw = path.read_bytes()
    file_hash = hashlib.sha256(raw).hexdigest()
    leaf_preimage = b"mend-release-leaf-v1\0" + relative.encode() + b"\0" + file_hash.encode()
    leaf_hash = h(leaf_preimage)
    leaves.append({
        "path": relative,
        "bytes": len(raw),
        "file_sha256": file_hash,
        "leaf_sha256": leaf_hash.hex(),
    })

level = [bytes.fromhex(x["leaf_sha256"]) for x in leaves]
levels = [len(level)]
while len(level) > 1:
    if len(level) % 2:
        level = level + [level[-1]]
    level = [
        h(b"mend-release-node-v1\0" + level[i] + level[i + 1])
        for i in range(0, len(level), 2)
    ]
    levels.append(len(level))

receipt = {
    "schema_version": "mend.public_release_receipt.v1",
    "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "root_kind": "MEND_PUBLIC_RELEASE_MERKLE_V1",
    "hash": "SHA-256",
    "leaf_order": "lexicographic path",
    "leaf_preimage": "b'mend-release-leaf-v1\\0' || UTF8(path) || NUL || ASCII(file_sha256_hex)",
    "node_preimage": "b'mend-release-node-v1\\0' || left_digest_bytes || right_digest_bytes",
    "odd_node_rule": "duplicate final node",
    "canonical_leaf_count": len(leaves),
    "tree_widths": levels,
    "canonical_leaves": leaves,
    "merkle_root_sha256": level[0].hex(),
    "scope_note": "Root covers the declared public artifact files above. It does not establish truth, causality, clinical validity, or compliance.",
}
RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n")
print(receipt["merkle_root_sha256"])
