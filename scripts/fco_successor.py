#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON = "RFC8785-like JSON: UTF-8, sorted keys, separators comma/colon, ensure_ascii=false"
STATES = {"PROPOSED","IMPLEMENTED","EXECUTED","OBSERVED","SUPPORTED","FAILED","NEGATIVE","NULL","DEFERRED","NOT_TESTED","UNKNOWN","NOT_COMPUTED"}
BP_DIR = ROOT / "breakpoints"
FCO_DIR = ROOT / "fco"
CLAIM = "Integrity of declared leaves only; not scientific truth, causal proof, clinical validity, security completeness, or regulatory compliance."

def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")

def make_fco(fco_type: str, execution_state: str, payload: dict, **fields: object) -> dict:
    if execution_state not in STATES:
        raise ValueError(execution_state)
    body = {"fco_type": fco_type, "canonicalization": CANON, "execution_state": execution_state, "payload": payload, **fields}
    digest = sha(canonical(body))
    return {"fco_id": f"fco_{digest}", "content_sha256": digest, **body}

def load(name: str) -> dict:
    return json.loads((FCO_DIR / name).read_text())

def breakpoint(number: int, bp_id: str, kind: str, parent_id: str, parent_root: str, paths: list[str], state: str = "OBSERVED") -> dict:
    leaves=[]
    for logical in sorted(paths):
        raw=(ROOT/logical).read_bytes(); file_hash=sha(raw)
        leaf_hash=sha(b"mend-fco-leaf-v1\0"+logical.encode()+b"\0"+file_hash.encode())
        leaves.append({"logical_path":logical,"artifact_type":kind,"bytes":len(raw),"file_sha256":file_hash,"leaf_sha256":leaf_hash})
    level=[bytes.fromhex(x["leaf_sha256"]) for x in leaves]
    while len(level)>1:
        if len(level)%2: level.append(level[-1])
        level=[hashlib.sha256(b"mend-fco-node-v1\0"+level[i]+level[i+1]).digest() for i in range(0,len(level),2)]
    manifest={"schema_version":"mend.breakpoint.v2","breakpoint_id":bp_id,"root_kind":kind,"hash_algorithm":"SHA-256","parent_breakpoint_id":parent_id,"parent_root_sha256":parent_root,"git_commit_if_available":subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,text=True,capture_output=True,check=True).stdout.strip(),"canonical_leaf_count":len(leaves),"canonical_leaf_order":"lexicographic logical_path","canonicalization":"raw file bytes; SHA-256 lowercase hex","leaf_preimage_definition":"b'mend-fco-leaf-v1\\0' || UTF8(logical_path) || NUL || ASCII(file_sha256_hex)","node_preimage_definition":"b'mend-fco-node-v1\\0' || left_digest_bytes || right_digest_bytes","odd_node_rule":"duplicate final node","canonical_leaves":leaves,"merkle_root_sha256":level[0].hex(),"execution_state":state,"scope_note":f"Sequential checkpoint BP{number}; only artifacts available at this phase.","claim_boundary":CLAIM}
    write_json(BP_DIR/f"bp{number}_{bp_id.lower()}.json",manifest)
    print(f"BP{number}_ROOT={manifest['merkle_root_sha256']}")
    return manifest

def atomize() -> None:
    source_path="data/core/synthetic_fhir_bundle.json"; raw=(ROOT/source_path).read_bytes()
    source=make_fco("SOURCE_FCO","OBSERVED",{"logical_path":source_path,"media_type":"application/fhir+json","record_class":"synthetic_fixture"},parent_fco_ids=[],source_ref=source_path,source_date="2026-09-26",retrieval_time="2026-09-26T00:00:00Z",creation_time="2026-09-26T00:00:00Z",freshness_days=0,freshness_class="FRESH",rights_class="PUBLIC_REPOSITORY_FIXTURE",sensitivity_class="SYNTHETIC",purpose="research",transformation="IDENTITY",executor="MEND_DETERMINISTIC_ATOMIZER_V1",input_sha256=sha(raw),verification_state="SUPPORTED",release_state="NOT_COMPUTED",policy_ref="MEND_SYNTHETIC_RESEARCH_V1",provenance_refs=[source_path],breakpoint_ref="MEND_CORE_20260926_B1")
    write_json(FCO_DIR/"source.json",source)
    data=json.loads(raw); entries=data.get("entry",[])
    summary={"resource_count":len(entries),"resource_types":sorted({e.get("resource",{}).get("resourceType","UNKNOWN") for e in entries}),"fixture_sha256":sha(raw)}
    atom=make_fco("DATA_ATOM_FCO","OBSERVED",summary,parent_fco_ids=[source["fco_id"]],source_ref=source_path,source_date="2026-09-26",retrieval_time="2026-09-26T00:00:00Z",creation_time="2026-09-26T00:00:00Z",freshness_days=0,freshness_class="FRESH",rights_class="PUBLIC_REPOSITORY_FIXTURE",sensitivity_class="SYNTHETIC",purpose="research",transformation="DETERMINISTIC_MINIMIZATION",executor="MEND_DETERMINISTIC_ATOMIZER_V1",input_sha256=sha(raw),verification_state="SUPPORTED",release_state="NOT_COMPUTED",policy_ref="MEND_SYNTHETIC_RESEARCH_V1",provenance_refs=[source["fco_id"]],breakpoint_ref="NOT_COMPUTED")
    write_json(FCO_DIR/"data_atom.json",atom)

def route() -> None:
    atom=load("data_atom.json")
    prompt="Using only this synthetic summary, provide one bounded research advisory observation. Do not infer identity, diagnosis, treatment, compliance, or clinical validity. Summary: "+json.dumps(atom["payload"],sort_keys=True)
    params={"maxTokens":160,"temperature":0.0}
    req=make_fco("MODEL_REQUEST_FCO","PROPOSED",{"task_class":"BOUNDED_SYNTHETIC_HEALTH_ADVISORY","prompt":prompt,"parameters":params},parent_fco_ids=[atom["fco_id"]],purpose="research",sensitivity_class="SYNTHETIC",transformation="REQUEST_ADVISORY",executor="MEND_ROUTER_V1",provider="UNKNOWN",model_id="UNKNOWN",model_version="UNKNOWN",inference_profile="UNKNOWN",prompt_sha256=sha(prompt.encode()),parameters_sha256=sha(canonical(params)),input_sha256=atom["content_sha256"],verification_state="NOT_COMPUTED",release_state="NOT_COMPUTED",policy_ref="MEND_MODEL_ROUTING_V1",provenance_refs=[atom["fco_id"]],breakpoint_ref="MEND_SOURCE_ATOM_BREAKPOINT_V1")
    write_json(FCO_DIR/"model_request.json",req)
    route_payload={"task_class":"BOUNDED_SYNTHETIC_HEALTH_ADVISORY","purpose":"research","sensitivity_class":"SYNTHETIC","candidate_providers":[{"provider":"LOCAL","state":"NOT_TESTED"},{"provider":"AMAZON_BEDROCK","state":"IMPLEMENTED"},{"provider":"OPENROUTER","state":"NOT_TESTED"}],"candidate_models":["amazon.nova-micro-v1:0"],"selected_provider":"AMAZON_BEDROCK","selected_model":"amazon.nova-micro-v1:0","selection_reason":"Dynamically discovered low-cost text model suitable for bounded synthetic advisory inference.","privacy_constraint":"SYNTHETIC_ONLY","cost_class":"LOW","latency_class":"INTERACTIVE","fallback_order":["AMAZON_BEDROCK","LOCAL","OPENROUTER"],"routing_policy_version":"MEND_MODEL_ROUTING_V1"}
    route_fco=make_fco("MODEL_ROUTE_FCO","SUPPORTED",route_payload,parent_fco_ids=[req["fco_id"]],purpose="research",sensitivity_class="SYNTHETIC",transformation="POLICY_AWARE_ROUTE_SELECTION",executor="MEND_ROUTER_V1",provider="AMAZON_BEDROCK",model_id="amazon.nova-micro-v1:0",model_version="1:0",inference_profile="us.amazon.nova-micro-v1:0",prompt_sha256=req["prompt_sha256"],parameters_sha256=req["parameters_sha256"],input_sha256=req["content_sha256"],verification_state="SUPPORTED",release_state="NOT_COMPUTED",policy_ref="MEND_MODEL_ROUTING_V1",provenance_refs=[req["fco_id"]],breakpoint_ref="NOT_COMPUTED")
    write_json(FCO_DIR/"model_route.json",route_fco)

def execute() -> None:
    req=load("model_request.json"); route_fco=load("model_route.json")
    started=datetime.now(timezone.utc); before=time.monotonic()
    messages=[{"role":"user","content":[{"text":req["payload"]["prompt"]}]}]
    cmd=["aws","bedrock-runtime","converse","--region","us-east-1","--model-id",route_fco["inference_profile"],"--messages",json.dumps(messages,separators=(",",":")),"--inference-config",json.dumps(req["payload"]["parameters"],separators=(",",":")),"--output","json","--no-cli-pager"]
    proc=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
    finished=datetime.now(timezone.utc); latency=int((time.monotonic()-before)*1000)
    if proc.returncode:
        error_class="AccessDeniedException" if "AccessDenied" in proc.stderr else "ValidationException" if "ValidationException" in proc.stderr else "BedrockInvocationError"
        receipt={"provider":"AMAZON_BEDROCK","region":"us-east-1","model_id":route_fco["model_id"],"inference_profile_id":route_fco["inference_profile"],"execution_state":"FAILED","error_class":error_class,"latency_ms":latency}
        write_json(ROOT/"receipts/bedrock_execution.json",receipt); raise SystemExit(error_class)
    response=json.loads(proc.stdout); text=response["output"]["message"]["content"][0]["text"]
    usage=response.get("usage",{})
    result=make_fco("MODEL_RESULT_FCO","OBSERVED",{"advisory_text":text,"claim_boundary":"Probabilistic advisory over synthetic data; not clinical guidance."},parent_fco_ids=[route_fco["fco_id"]],purpose="research",sensitivity_class="SYNTHETIC",transformation="BEDROCK_MODEL_INFERENCE",executor="AMAZON_BEDROCK_RUNTIME",provider="AMAZON_BEDROCK",model_id=route_fco["model_id"],model_version=route_fco["model_version"],inference_profile=route_fco["inference_profile"],prompt_sha256=req["prompt_sha256"],parameters_sha256=req["parameters_sha256"],input_sha256=req["input_sha256"],execution_started=started.isoformat().replace("+00:00","Z"),execution_finished=finished.isoformat().replace("+00:00","Z"),latency_ms=latency,result_sha256=sha(text.encode()),verification_state="NOT_COMPUTED",release_state="NOT_COMPUTED",policy_ref="MEND_MODEL_ROUTING_V1",provenance_refs=[route_fco["fco_id"]],breakpoint_ref="MEND_MODEL_ROUTE_BREAKPOINT_V1")
    write_json(FCO_DIR/"model_result.json",result)
    execution=make_fco("MODEL_EXECUTION_FCO","EXECUTED",{"provider_state":"AUTHENTICATED_AND_EXECUTED","region":"us-east-1","request_sha256":sha(canonical(messages)),"usage":usage,"cost_metadata":"NOT_COMPUTED"},parent_fco_ids=[route_fco["fco_id"]],purpose="research",sensitivity_class="SYNTHETIC",transformation="BEDROCK_CONVERSE",executor="AWS_CLI_BEDROCK_RUNTIME",provider="AMAZON_BEDROCK",model_id=route_fco["model_id"],model_version=route_fco["model_version"],inference_profile=route_fco["inference_profile"],prompt_sha256=req["prompt_sha256"],parameters_sha256=req["parameters_sha256"],input_sha256=req["input_sha256"],execution_started=result["execution_started"],execution_finished=result["execution_finished"],latency_ms=latency,result_sha256=result["result_sha256"],verification_state="NOT_COMPUTED",release_state="NOT_COMPUTED",policy_ref="MEND_MODEL_ROUTING_V1",provenance_refs=[route_fco["fco_id"],result["fco_id"]],breakpoint_ref="MEND_MODEL_ROUTE_BREAKPOINT_V1")
    write_json(FCO_DIR/"model_execution.json",execution)
    write_json(ROOT/"receipts/bedrock_execution.json",{"schema_version":"mend.bedrock.receipt.v1","provider":"AMAZON_BEDROCK","region":"us-east-1","model_id":route_fco["model_id"],"inference_profile_id":route_fco["inference_profile"],"execution_state":"EXECUTED","request_sha256":execution["payload"]["request_sha256"],"result_sha256":result["result_sha256"],"latency_ms":latency,"usage":usage})

def verify() -> None:
    result=load("model_result.json"); text=result["payload"]["advisory_text"]
    forbidden=["MEND-DEMO-ALPHA-001","Patient/alpha-001","Observation/alpha-lab-001"]
    challenges={"nonempty":bool(text.strip()),"result_hash_match":sha(text.encode())==result["result_sha256"],"explicit_identifier_absent":not any(x in text for x in forbidden),"claim_boundary_present":"not clinical guidance" in result["payload"]["claim_boundary"].lower()}
    state="SUPPORTED" if all(challenges.values()) else "FAILED"
    fco=make_fco("ANTIGENCE_VERIFICATION_FCO",state,{"verification_method":"ANTIGENCE_ADAPTER_DETERMINISTIC_CHALLENGE_V1","challenge_result":challenges,"limitations":["No scientific truth validation","No causal validation","No clinical validation","No compliance determination"]},parent_fco_ids=[result["fco_id"]],purpose="research",sensitivity_class="SYNTHETIC",transformation="DETERMINISTIC_CHALLENGE",executor="LOCAL_ANTIGENCE_ADAPTER",provider="LOCAL",model_id="NULL",model_version="NULL",inference_profile="NULL",input_sha256=result["result_sha256"],result_sha256=sha(canonical(challenges)),verification_state=state,release_state="NOT_COMPUTED",policy_ref="MEND_ANTIGENCE_VERIFICATION_V1",provenance_refs=[result["fco_id"]],breakpoint_ref="MEND_MODEL_EXECUTION_BREAKPOINT_V1")
    write_json(FCO_DIR/"antigence_verification.json",fco)

def release() -> None:
    verification=load("antigence_verification.json"); result=load("model_result.json")
    allowed=verification["verification_state"]=="SUPPORTED" and verification["payload"]["challenge_result"]["explicit_identifier_absent"]
    state="SUPPORTED" if allowed else "FAILED"
    decision=make_fco("RELEASE_DECISION_FCO",state,{"decision":"AUTHORIZED" if allowed else "BLOCKED","authority":"DETERMINISTIC_MEND_POLICY_GATE","purpose":"research","rules":{"synthetic_only":True,"explicit_identifiers_excluded":True,"verification_required":True}},parent_fco_ids=[verification["fco_id"]],purpose="research",sensitivity_class="SYNTHETIC",transformation="DETERMINISTIC_POLICY_EVALUATION",executor="MEND_POLICY_GATE_V1",provider="LOCAL",model_id="NULL",input_sha256=verification["content_sha256"],verification_state=verification["verification_state"],release_state="SUPPORTED" if allowed else "FAILED",policy_ref="MEND_SYNTHETIC_RESEARCH_RELEASE_V1",provenance_refs=[verification["fco_id"]],breakpoint_ref="MEND_VERIFICATION_BREAKPOINT_V1")
    write_json(FCO_DIR/"release_decision.json",decision)
    released={"purpose":"research","advisory_text":result["payload"]["advisory_text"],"source_result_sha256":result["result_sha256"],"claim_boundary":result["payload"]["claim_boundary"]} if allowed else {"purpose":"research","blocked":True}
    release_fco=make_fco("RELEASE_FCO","SUPPORTED" if allowed else "FAILED",released,parent_fco_ids=[decision["fco_id"]],purpose="research",sensitivity_class="PUBLIC_SYNTHETIC_OUTPUT" if allowed else "SYNTHETIC",transformation="PURPOSE_BOUND_RELEASE",executor="MEND_POLICY_GATE_V1",provider="LOCAL",model_id="NULL",input_sha256=result["result_sha256"],result_sha256=sha(canonical(released)),verification_state=verification["verification_state"],release_state="SUPPORTED" if allowed else "FAILED",policy_ref="MEND_SYNTHETIC_RESEARCH_RELEASE_V1",provenance_refs=[decision["fco_id"],result["fco_id"]],breakpoint_ref="NOT_COMPUTED")
    write_json(FCO_DIR/"release.json",release_fco)
    write_json(ROOT/"receipts/egress_test.json",{"schema_version":"mend.egress.v1","execution_state":"EXECUTED","explicit_identifier_egress":"PASS" if allowed else "FAIL","claim_boundary":"Fixture scan only; no general compliance claim."})

def graph() -> None:
    names=["source","data_atom","model_request","model_route","model_execution","model_result","antigence_verification","release_decision","release"]
    fs={n:load(n+".json") for n in names}
    edges=[
      ("data_atom","DERIVED_FROM","source"),("source","HAS_ATOM","data_atom"),("data_atom","REQUESTED","model_request"),("model_request","ROUTED_BY","model_route"),("model_route","ROUTED_TO","model_execution"),("model_route","EXECUTED_BY","model_execution"),("model_execution","PRODUCED","model_result"),("model_result","VERIFIED_BY","antigence_verification"),("antigence_verification","CHALLENGED_BY","model_result"),("antigence_verification","AUTHORIZED_BY","release_decision"),("release_decision","RELEASED_AS","release")]
    graph={"schema_version":"mend.fcg.v2","nodes":[{"fco_id":x["fco_id"],"fco_type":x["fco_type"],"execution_state":x["execution_state"],"content_sha256":x["content_sha256"]} for x in fs.values()],"edges":[{"source":fs[a]["fco_id"],"type":t,"target":fs[b]["fco_id"]} for a,t,b in edges],"candidate_routes":[{"provider":"LOCAL","state":"NOT_TESTED"},{"provider":"OPENROUTER","state":"NOT_TESTED"}],"selected_route":{"provider":"AMAZON_BEDROCK","state":"EXECUTED"}}
    write_json(ROOT/"fcg/successor_fcg.json",graph)

def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("stage",choices=["bp1","atomize","bp2","route","bp3","execute","bp4","verify","bp5","release","bp6","graph","bp7"]); a=p.parse_args()
    parents={1:("MEND_PREDECESSOR_RECOVERY_V1","bba5e3fbbdcac3ca94e0507a3507326531e753c87b288394f452116b61f0443f")}
    if a.stage=="bp1": breakpoint(1,"MEND_FCO_SCHEMA_BREAKPOINT_V1","MEND_FCO_SCHEMA_MERKLE_V1",*parents[1],["schemas/fco.schema.json","schemas/fcg.schema.json","scripts/fco_successor.py","tests/test_fco_successor.py"])
    elif a.stage=="atomize": atomize()
    elif a.stage=="bp2":
        b=json.loads(next(BP_DIR.glob("bp1_*.json")).read_text()); breakpoint(2,"MEND_SOURCE_ATOM_BREAKPOINT_V1","MEND_SOURCE_ATOM_MERKLE_V1",b["breakpoint_id"],b["merkle_root_sha256"],["fco/source.json","fco/data_atom.json"])
    elif a.stage=="route": route()
    elif a.stage=="bp3":
        b=json.loads(next(BP_DIR.glob("bp2_*.json")).read_text()); breakpoint(3,"MEND_MODEL_ROUTE_BREAKPOINT_V1","MEND_MODEL_ROUTE_MERKLE_V1",b["breakpoint_id"],b["merkle_root_sha256"],["fco/model_request.json","fco/model_route.json"])
    elif a.stage=="execute": execute()
    elif a.stage=="bp4":
        b=json.loads(next(BP_DIR.glob("bp3_*.json")).read_text()); breakpoint(4,"MEND_MODEL_EXECUTION_BREAKPOINT_V1","MEND_MODEL_EXECUTION_MERKLE_V1",b["breakpoint_id"],b["merkle_root_sha256"],["fco/model_execution.json","fco/model_result.json","receipts/bedrock_execution.json"])
    elif a.stage=="verify": verify()
    elif a.stage=="bp5":
        b=json.loads(next(BP_DIR.glob("bp4_*.json")).read_text()); breakpoint(5,"MEND_VERIFICATION_BREAKPOINT_V1","MEND_VERIFICATION_MERKLE_V1",b["breakpoint_id"],b["merkle_root_sha256"],["fco/model_result.json","fco/antigence_verification.json"])
    elif a.stage=="release": release()
    elif a.stage=="bp6":
        b=json.loads(next(BP_DIR.glob("bp5_*.json")).read_text()); breakpoint(6,"MEND_RELEASE_BREAKPOINT_V1","MEND_RELEASE_MERKLE_V1",b["breakpoint_id"],b["merkle_root_sha256"],["fco/release_decision.json","fco/release.json","receipts/egress_test.json"])
    elif a.stage=="graph": graph()
    elif a.stage=="bp7":
        b=json.loads(next(BP_DIR.glob("bp6_*.json")).read_text()); paths=[str(p.relative_to(ROOT)) for p in FCO_DIR.glob("*.json")]+["fcg/successor_fcg.json","schemas/fco.schema.json","schemas/fcg.schema.json"]; breakpoint(7,"MEND_FCG_BREAKPOINT_V1","MEND_FCG_MERKLE_V1",b["breakpoint_id"],b["merkle_root_sha256"],paths)

if __name__=="__main__": main()
