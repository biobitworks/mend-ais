#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "breakpoints/mend_core_breakpoint_v1.json"
PARENT_RELEASE_ROOT = "06d020a06d21c99b6e39672e819e9b8a1dcfb8f29e0d92a1109afe4a8873a737"
PARENT_COMMIT = "f9c1be0bc7eacfaeeee819067d1c82d35e2f13c0"

CORE_FILES = [
    "AGENTS.md",
    "README.md",
    "agent_manifest.json",
    "data/core/synthetic_fhir_bundle.json",
    "docs/ARCHITECTURE.md",
    "docs/JUDGE_NAVIGATION.md",
    "fcg/core_fcg.json",
    "receipts/demo_research_20260926.json",
    "receipts/node_resource_audit_20260926.json",
    "sdk/js/mend-sdk.js",
    "sdk/python/mend_sdk.py",
    "server.py",
    "scripts/create_breakpoint.py",
    "scripts/enroll_local_node.py",
    "scripts/seal_release.py",
    "scripts/stop.sh",
    "scripts/unlock_local.py",
    "scripts/verify_breakpoint.py",
    "scripts/smoke.sh",
    "scripts/start_local.sh",
    "scripts/status.sh",
    "scripts/verify_fcg.py",
    "web/index.html",
]

def h(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()

leaves = []
for relative in sorted(CORE_FILES):
    path = ROOT / relative
    raw = path.read_bytes()
    file_hash = hashlib.sha256(raw).hexdigest()
    preimage = b"mend-core-leaf-v1\0" + relative.encode() + b"\0" + file_hash.encode()
    leaf_hash = h(preimage)
    leaves.append({
        "path": relative,
        "bytes": len(raw),
        "file_sha256": file_hash,
        "leaf_sha256": leaf_hash.hex(),
    })

level = [bytes.fromhex(x["leaf_sha256"]) for x in leaves]
widths = [len(level)]
while len(level) > 1:
    if len(level) % 2:
        level = level + [level[-1]]
    level = [
        h(b"mend-core-node-v1\0" + level[i] + level[i + 1])
        for i in range(0, len(level), 2)
    ]
    widths.append(len(level))

manifest = {
    "schema_version": "mend.breakpoint.v1",
    "breakpoint_id": "MEND_CORE_20260926_B1",
    "root_kind": "MEND_CORE_CAPABILITY_MERKLE_V1",
    "hash": "SHA-256",
    "parent": {
        "public_release_root_sha256": PARENT_RELEASE_ROOT,
        "git_commit": PARENT_COMMIT,
    },
    "canonical_leaf_count": len(leaves),
    "leaf_order": "lexicographic path",
    "leaf_preimage": "b'mend-core-leaf-v1\\0' || UTF8(path) || NUL || ASCII(file_sha256_hex)",
    "node_preimage": "b'mend-core-node-v1\\0' || left_digest_bytes || right_digest_bytes",
    "odd_node_rule": "duplicate final node",
    "tree_widths": widths,
    "canonical_leaves": leaves,
    "merkle_root_sha256": level[0].hex(),
    "unlock_protocol": {
        "kind": "LOCAL_CAPABILITY_DESCRIPTOR_V1",
        "descriptor_location": "user config directory; never committed",
        "binding": "descriptor.breakpoint_root_sha256 must equal this merkle root",
        "public_secrets": "NONE",
        "authorization_boundary": "possession of local machine account and descriptor",
    },
    "claim_boundary": "This breakpoint establishes identity/integrity of the declared core files only; it does not establish truth, causality, clinical validity, compliance, or device authorization.",
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(manifest, indent=2) + "\n")
print(manifest["merkle_root_sha256"])
