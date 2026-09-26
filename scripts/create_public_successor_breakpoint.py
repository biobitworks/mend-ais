#!/usr/bin/env python3
import hashlib,json,subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[1]
parent=json.loads(next((root/"breakpoints").glob("bp7_*.json")).read_text())
excluded={"breakpoints/bp8_mend_public_successor_merkle_v1.json"}
paths=[]
for path in root.rglob("*"):
 if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts or path.name == ".DS_Store": continue
 logical=str(path.relative_to(root))
 if logical not in excluded: paths.append(logical)
leaves=[]
for logical in sorted(paths):
 raw=(root/logical).read_bytes(); file_hash=hashlib.sha256(raw).hexdigest()
 leaf=hashlib.sha256(b"mend-fco-leaf-v1\0"+logical.encode()+b"\0"+file_hash.encode()).hexdigest()
 leaves.append({"logical_path":logical,"artifact_type":"MEND_PUBLIC_SUCCESSOR_MERKLE_V1","bytes":len(raw),"file_sha256":file_hash,"leaf_sha256":leaf})
level=[bytes.fromhex(x["leaf_sha256"]) for x in leaves]
while len(level)>1:
 if len(level)%2: level.append(level[-1])
 level=[hashlib.sha256(b"mend-fco-node-v1\0"+level[i]+level[i+1]).digest() for i in range(0,len(level),2)]
bp={"schema_version":"mend.breakpoint.v2","breakpoint_id":"MEND_PUBLIC_SUCCESSOR_MERKLE_V1","root_kind":"MEND_PUBLIC_SUCCESSOR_MERKLE_V1","hash_algorithm":"SHA-256","parent_breakpoint_id":parent["breakpoint_id"],"parent_root_sha256":parent["merkle_root_sha256"],"git_commit_if_available":subprocess.run(["git","rev-parse","HEAD"],cwd=root,text=True,capture_output=True,check=True).stdout.strip(),"canonical_leaf_count":len(leaves),"canonical_leaf_order":"lexicographic logical_path","canonicalization":"raw file bytes; SHA-256 lowercase hex","leaf_preimage_definition":"b'mend-fco-leaf-v1\\0' || UTF8(logical_path) || NUL || ASCII(file_sha256_hex)","node_preimage_definition":"b'mend-fco-node-v1\\0' || left_digest_bytes || right_digest_bytes","odd_node_rule":"duplicate final node","canonical_leaves":leaves,"merkle_root_sha256":level[0].hex(),"execution_state":"SUPPORTED","scope_note":"Public-safe successor artifact set finalized after tests and scans.","claim_boundary":"Integrity of declared leaves only; not scientific truth, causal proof, clinical validity, security completeness, or regulatory compliance."}
out=root/"breakpoints/bp8_mend_public_successor_merkle_v1.json"; out.write_text(json.dumps(bp,indent=2)+"\n")
print("BP8_ROOT="+bp["merkle_root_sha256"])
