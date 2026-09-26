#!/usr/bin/env python3
import hashlib,json,sys
from pathlib import Path

root=Path(__file__).resolve().parents[1]
ok=True
def check(label, value):
 global ok
 print(f"{label}={'PASS' if value else 'FAIL'}"); ok &= value

previous=None
for number in range(9):
 matches=sorted((root/"breakpoints").glob(f"bp{number}_*.json"))
 if not matches: check(f"BP{number}",False); continue
 bp=json.loads(matches[-1].read_text())
 leaves=bp["canonical_leaves"]
 paths=[l["logical_path"] for l in leaves]
 current=paths==sorted(set(paths))
 for leaf in leaves:
  path=root/leaf["logical_path"]
  file_hash=hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
  expected_leaf=hashlib.sha256(
   b"mend-fco-leaf-v1\0"+leaf["logical_path"].encode()+b"\0"+leaf["file_sha256"].encode()
  ).hexdigest()
  current &= file_hash==leaf["file_sha256"] and expected_leaf==leaf["leaf_sha256"]
 level=[bytes.fromhex(l["leaf_sha256"]) for l in leaves]
 while len(level)>1:
  if len(level)%2: level.append(level[-1])
  level=[hashlib.sha256(b"mend-fco-node-v1\0"+level[i]+level[i+1]).digest() for i in range(0,len(level),2)]
 chain=previous is None or bp["parent_root_sha256"]==previous["merkle_root_sha256"]
 check(f"BP{number}",current and level[0].hex()==bp["merkle_root_sha256"] and chain)
 previous=bp

fcos=[json.loads(p.read_text()) for p in sorted((root/"fco").glob("*.json"))]
ids={f["fco_id"] for f in fcos}
identity=True
for f in fcos:
 body={k:v for k,v in f.items() if k not in {"fco_id","content_sha256"}}
 digest=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
 identity &= f["fco_id"]=="fco_"+digest and f["content_sha256"]==digest
check("FCO_IDENTITY",identity)
graph=json.loads((root/"fcg/successor_fcg.json").read_text()); external={x["id"] for x in graph.get("external_nodes",[])}
check("FCG_EDGE_VALIDATION",all(e["source"] in ids and e["target"] in ids|external for e in graph["edges"]))
check("MODEL_ROUTE_FCO_CREATED_BEFORE_RESULT",not any(l["logical_path"]=="fco/model_result.json" for l in json.loads(next((root/"breakpoints").glob("bp3_*.json")).read_text())["canonical_leaves"]))
check("EXPLICIT_IDENTIFIER_EGRESS",json.loads((root/"receipts/egress_test.json").read_text())["explicit_identifier_egress"]=="PASS")
sys.exit(0 if ok else 1)
