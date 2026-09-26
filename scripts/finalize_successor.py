#!/usr/bin/env python3
import hashlib, json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
canon=lambda x:json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
bp6=json.loads(next((root/"breakpoints").glob("bp6_*.json")).read_text())
release=json.loads((root/"fco/release.json").read_text())
body={
 "fco_type":"BREAKPOINT_FCO","canonicalization":"RFC8785-like JSON: UTF-8, sorted keys, separators comma/colon, ensure_ascii=false","execution_state":"OBSERVED",
 "payload":{"breakpoint_id":bp6["breakpoint_id"],"merkle_root_sha256":bp6["merkle_root_sha256"],"leaf_count":bp6["canonical_leaf_count"]},
 "parent_fco_ids":[release["fco_id"]],"purpose":"research","sensitivity_class":"PUBLIC_SYNTHETIC_OUTPUT","transformation":"MERKLE_SEAL","executor":"MEND_BREAKPOINT_ENGINE_V1","provider":"LOCAL","model_id":"NULL","input_sha256":release["content_sha256"],"verification_state":"SUPPORTED","release_state":"SUPPORTED","policy_ref":"MEND_BREAKPOINT_POLICY_V1","provenance_refs":["breakpoints/"+next((root/"breakpoints").glob("bp6_*.json")).name],"breakpoint_ref":bp6["breakpoint_id"]}
digest=hashlib.sha256(canon(body)).hexdigest(); fco={"fco_id":"fco_"+digest,"content_sha256":digest,**body}
(root/"fco/breakpoint.json").write_text(json.dumps(fco,indent=2)+"\n")
graph=json.loads((root/"fcg/successor_fcg.json").read_text())
graph["nodes"].append({"fco_id":fco["fco_id"],"fco_type":fco["fco_type"],"execution_state":fco["execution_state"],"content_sha256":fco["content_sha256"]})
graph["edges"].extend([
 {"source":release["fco_id"],"type":"SEALED_BY","target":fco["fco_id"]},
 {"source":fco["fco_id"],"type":"SUCCESSOR_OF","target":"MEND_CORE_20260926_B1"}
])
graph["external_nodes"]=[{"id":"MEND_CORE_20260926_B1","type":"PREDECESSOR_BREAKPOINT","state":"SUPPORTED"}]
(root/"fcg/successor_fcg.json").write_text(json.dumps(graph,indent=2)+"\n")
print("BREAKPOINT_FCO=PASS")
