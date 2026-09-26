#!/usr/bin/env python3
import hashlib, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
fcg = json.loads((ROOT / "fcg/core_fcg.json").read_text())
nodes = {node["id"]: node for node in fcg["nodes"]}
errors = []

for edge in fcg["edges"]:
    if edge["from"] not in nodes:
        errors.append(f"missing edge source: {edge}")
    if edge["to"] not in nodes:
        errors.append(f"missing edge target: {edge}")

dataset = ROOT / "data/core/synthetic_fhir_bundle.json"
actual = hashlib.sha256(dataset.read_bytes()).hexdigest()
expected = nodes["dataset.synthetic_fhir_core_v1"]["content_sha256"]
if actual != expected:
    errors.append(f"dataset hash mismatch: {actual} != {expected}")

if fcg.get("root_kind") != "NONE_NOT_COMPUTED":
    errors.append("Unexpected root declaration. This public FCG currently declares no Merkle root.")

if errors:
    print("FAIL")
    for error in errors:
        print(error)
    sys.exit(1)

print("PASS: FCG edge references")
print("PASS: dataset content SHA-256")
print("PASS: no uncomputed Merkle root claimed")
