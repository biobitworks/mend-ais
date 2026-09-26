#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import os
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BREAKPOINT = ROOT / "breakpoints/mend_core_breakpoint_v1.json"
DESCRIPTOR = Path.home() / ".config" / "mend-ais" / "unlock.json"

parser = argparse.ArgumentParser(description="Resolve machine-local Mend capabilities without publishing local paths.")
parser.add_argument("--list", action="store_true", help="List capability keys and state only.")
parser.add_argument("--capability", help="Return one local capability object.")
parser.add_argument("--json", action="store_true", help="Emit JSON.")
args = parser.parse_args()

if not DESCRIPTOR.is_file():
    payload = {"status": "LOCKED", "reason": "LOCAL_DESCRIPTOR_NOT_PRESENT"}
    print(json.dumps(payload) if args.json else "LOCKED: LOCAL_DESCRIPTOR_NOT_PRESENT")
    sys.exit(3)

mode = stat.S_IMODE(DESCRIPTOR.stat().st_mode)
if mode & (stat.S_IRWXG | stat.S_IRWXO):
    payload = {"status": "LOCKED", "reason": "DESCRIPTOR_PERMISSIONS_TOO_BROAD"}
    print(json.dumps(payload) if args.json else "LOCKED: DESCRIPTOR_PERMISSIONS_TOO_BROAD")
    sys.exit(4)

bp = json.loads(BREAKPOINT.read_text())
d = json.loads(DESCRIPTOR.read_text())
if d.get("breakpoint_root_sha256") != bp.get("merkle_root_sha256"):
    payload = {
        "status": "LOCKED",
        "reason": "BREAKPOINT_BINDING_MISMATCH",
        "expected_breakpoint_root_sha256": bp.get("merkle_root_sha256"),
    }
    print(json.dumps(payload) if args.json else "LOCKED: BREAKPOINT_BINDING_MISMATCH")
    sys.exit(5)

caps = d.get("capabilities", {})
if args.capability:
    if args.capability not in caps:
        payload = {"status": "LOCKED", "reason": "CAPABILITY_NOT_ENROLLED", "capability": args.capability}
        print(json.dumps(payload) if args.json else "LOCKED: CAPABILITY_NOT_ENROLLED")
        sys.exit(6)
    payload = {
        "status": "UNLOCKED",
        "node_id": d.get("node_id"),
        "breakpoint_root_sha256": d.get("breakpoint_root_sha256"),
        "capability": args.capability,
        "value": caps[args.capability],
    }
    print(json.dumps(payload, indent=2) if args.json else json.dumps(payload["value"], indent=2))
elif args.list or not args.capability:
    public_caps = {
        k: {
            "enrolled": True,
            "has_path": bool(v.get("path")) if isinstance(v, dict) else False,
            "has_url": bool(v.get("url")) if isinstance(v, dict) else False,
            "state": v.get("state") if isinstance(v, dict) else None,
        }
        for k, v in sorted(caps.items())
    }
    payload = {
        "status": "UNLOCKED",
        "node_id": d.get("node_id"),
        "breakpoint_root_sha256": d.get("breakpoint_root_sha256"),
        "capabilities": public_caps,
    }
    print(json.dumps(payload, indent=2))
