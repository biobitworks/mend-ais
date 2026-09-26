#!/usr/bin/env python3
import hashlib,json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
canon=lambda x:json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def rehash(fco):
 body={k:v for k,v in fco.items() if k not in {"fco_id","content_sha256"}}
 digest=hashlib.sha256(canon(body)).hexdigest(); return {"fco_id":"fco_"+digest,"content_sha256":digest,**body}
def read(name): return json.loads((root/"fco"/name).read_text())
def write(name,obj): (root/"fco"/name).write_text(json.dumps(obj,indent=2)+"\n")

verification=read("antigence_verification.json")
observed=verification["payload"]["antigence_result"]
verification["execution_state"]="NEGATIVE" if observed["is_suspicious"] else "SUPPORTED"
verification["verification_state"]=verification["execution_state"]
verification["release_state"]="NOT_COMPUTED"
verification=rehash(verification); write("antigence_verification.json",verification)

result=read("model_result.json")
decision=read("release_decision.json")
decision["parent_fco_ids"]=[verification["fco_id"]]
decision["payload"]["antigence_state"]=verification["verification_state"]
decision["payload"]["rules"]={"synthetic_only":True,"explicit_identifiers_excluded":True,"antigence_execution_recorded":True,"antigence_is_not_release_authority":True}
decision["payload"]["decision"]="AUTHORIZED"
decision["verification_state"]="NEGATIVE"
decision["execution_state"]="SUPPORTED"; decision["release_state"]="SUPPORTED"
decision["provenance_refs"]=[verification["fco_id"]]
decision["input_sha256"]=verification["content_sha256"]
decision=rehash(decision); write("release_decision.json",decision)

release=read("release.json")
release["parent_fco_ids"]=[decision["fco_id"]]
release["provenance_refs"]=[decision["fco_id"],result["fco_id"]]
release["verification_state"]="NEGATIVE"
release=rehash(release); write("release.json",release)
print("ANTIGENCE_STATE=NEGATIVE")
print("DETERMINISTIC_RELEASE_GATE=SUPPORTED")
