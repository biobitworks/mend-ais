#!/usr/bin/env python3
import hashlib, json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
path=root/"fco/antigence_verification.json"
fco=json.loads(path.read_text())
receipt=json.loads((root/"receipts/antigence_runtime.json").read_text())
fco["payload"]["antigence_result"]={k:receipt[k] for k in ("runtime","runtime_version","execution_state","response","anomaly_count","total_checks","is_suspicious","limitations")}
fco["payload"]["verification_method"]="ANTIGENCE_LOGIC_ANTIBODY_PLUS_DETERMINISTIC_CHALLENGE_V1"
fco["executor"]="LOCAL_ANTIGENCE_RUNTIME_AND_MEND_ADAPTER"
fco["model_version"]=receipt["runtime_version"]
fco["provenance_refs"].append("receipts/antigence_runtime.json")
body={k:v for k,v in fco.items() if k not in {"fco_id","content_sha256"}}
raw=json.dumps(body,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
digest=hashlib.sha256(raw).hexdigest()
fco["fco_id"]="fco_"+digest; fco["content_sha256"]=digest
path.write_text(json.dumps(fco,indent=2)+"\n")
print("ANTIGENCE_FCO_BINDING=PASS")
