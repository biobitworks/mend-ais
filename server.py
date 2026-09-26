#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "data/core/synthetic_fhir_bundle.json"
FCG = ROOT / "fcg/core_fcg.json"
WEB = ROOT / "web"
MODEL = "longhorizon-liquid-230m:latest"
OLLAMA = "http://127.0.0.1:11434"
OLLARMA = "http://127.0.0.1:8484"

def load_json(path: Path):
    return json.loads(path.read_text())

def canonical_bytes(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()

def sha256_obj(obj) -> str:
    return hashlib.sha256(canonical_bytes(obj)).hexdigest()

def get_json(url: str, timeout: float = 2.5):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.load(response)

def post_json(url: str, payload: dict, timeout: float = 20.0):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)

def probe_services():
    result = {
        "ollama": {"status": "FAIL"},
        "ollarma": {"status": "FAIL"},
        "core_model": {"status": "UNKNOWN", "model": MODEL},
    }
    try:
        tags = get_json(OLLAMA + "/api/tags")
        models = [m.get("name") for m in tags.get("models", [])]
        result["ollama"] = {"status": "PASS", "models": models}
        result["core_model"]["status"] = "PASS" if MODEL in models else "FAIL"
    except Exception as exc:
        result["ollama"]["detail"] = str(exc)
    try:
        health = get_json(OLLARMA + "/health")
        result["ollarma"] = {
            "status": "PASS" if health.get("status") == "ready" else "DEGRADED",
            "reported_status": health.get("status"),
            "effective_model": health.get("helper_chat", {}).get("effective_model"),
            "reason_code": health.get("helper_chat", {}).get("reason_code"),
        }
    except Exception as exc:
        result["ollarma"]["detail"] = str(exc)
    return result

def resources(bundle):
    return [entry.get("resource", {}) for entry in bundle.get("entry", [])]

def first_resource(bundle, resource_type):
    return next((r for r in resources(bundle) if r.get("resourceType") == resource_type), {})

def extract_metrics(bundle):
    observations = [r for r in resources(bundle) if r.get("resourceType") == "Observation"]
    condition = first_resource(bundle, "Condition")
    out = {}
    for obs in observations:
        text = (obs.get("code", {}).get("text") or "").lower()
        if "a1c" in text or "hemoglobin a1c" in text:
            out["a1c_percent"] = obs.get("valueQuantity", {}).get("value")
        elif "wound area" in text:
            out["wound_area_cm2"] = obs.get("valueQuantity", {}).get("value")
        elif "tissue composition" in text:
            out["tissue_composition_percent"] = {
                c.get("code", {}).get("text"): c.get("valueQuantity", {}).get("value")
                for c in obs.get("component", [])
            }
    sites = condition.get("bodySite", [])
    out["wound_site"] = sites[0].get("text") if sites else None
    out["condition_code"] = (
        condition.get("code", {}).get("coding", [{}])[0].get("code")
        if condition.get("code", {}).get("coding") else None
    )
    return out

def forbidden_identifiers(bundle):
    patient = first_resource(bundle, "Patient")
    values = []
    for identifier in patient.get("identifier", []):
        values.append(str(identifier.get("value", "")))
    for name in patient.get("name", []):
        values.extend(str(x) for x in name.get("given", []))
        values.append(str(name.get("family", "")))
    values.append(str(patient.get("birthDate", "")))
    for telecom in patient.get("telecom", []):
        values.append(str(telecom.get("value", "")))
    for address in patient.get("address", []):
        values.extend(str(x) for x in address.get("line", []))
        values.extend(str(address.get(k, "")) for k in ("city", "postalCode"))
    return sorted({v for v in values if v})

def release_gate(bundle, purpose):
    patient = first_resource(bundle, "Patient")
    metrics = extract_metrics(bundle)
    source_hash = sha256_obj(bundle)
    base = {
        "schema": "mend.release.v1",
        "purpose": purpose,
        "source_sha256": source_hash,
        "clinical_metrics": metrics,
    }
    if purpose == "research":
        base["subject_key"] = hashlib.sha256(patient.get("id", "").encode()).hexdigest()[:16]
        base["policy"] = "research_minimum_v1"
    elif purpose == "treatment":
        base["subject"] = {
            "id": patient.get("id"),
            "name": patient.get("name"),
            "birthDate": patient.get("birthDate"),
        }
        base["policy"] = "treatment_synthetic_demo_v1"
    else:
        raise ValueError("unsupported purpose")
    return base

def model_advisory(bundle):
    metrics = extract_metrics(bundle)
    prompt = (
        "This is synthetic demo health data. Do not diagnose or recommend treatment. "
        "Summarize these structured facts in one short sentence and do not invent facts: "
        + json.dumps(metrics, sort_keys=True)
    )
    try:
        reply = post_json(OLLARMA + "/chat", {"prompt": prompt, "model": MODEL})
        return {
            "transport": "ollarma",
            "status": reply.get("status", "UNKNOWN"),
            "model": reply.get("model", MODEL),
            "text": reply.get("response", ""),
        }
    except Exception as first_exc:
        try:
            reply = post_json(
                OLLAMA + "/api/generate",
                {"model": MODEL, "prompt": prompt, "stream": False,
                 "options": {"temperature": 0, "num_predict": 96}},
            )
            return {
                "transport": "ollama_fallback",
                "status": "answered",
                "model": MODEL,
                "text": reply.get("response", ""),
                "primary_error": str(first_exc),
            }
        except Exception as second_exc:
            return {
                "transport": "none",
                "status": "FAIL",
                "model": MODEL,
                "text": "",
                "detail": f"ollarma={first_exc}; ollama={second_exc}",
            }

def demo(purpose):
    bundle = load_json(DATASET)
    release = release_gate(bundle, purpose)
    serialized = canonical_bytes(release).decode()
    hits = [value for value in forbidden_identifiers(bundle) if value in serialized]
    required_zero = purpose == "research"
    egress_pass = (not hits) if required_zero else True
    return {
        "demo_state": "EXECUTED",
        "dataset": {
            "id": bundle.get("id"),
            "synthetic": True,
            "sha256": sha256_obj(bundle),
        },
        "model_advisory": model_advisory(bundle),
        "release": release,
        "release_sha256": sha256_obj(release),
        "egress_scan": {
            "policy": "zero_explicit_identifiers" if required_zero else "purpose_allows_identity",
            "forbidden_hits": hits,
            "pass": egress_pass,
        },
        "claim_boundary": "Model output is advisory and is never the release authority.",
    }

class Handler(BaseHTTPRequestHandler):
    def _headers(self, status=200, content_type="application/json; charset=utf-8"):
        self.send_response(status)
        self.send_header("content-type", content_type)
        self.send_header("access-control-allow-origin", "*")
        self.send_header("cache-control", "no-store")
        self.end_headers()

    def send_json(self, obj, status=200):
        payload = json.dumps(obj, indent=2).encode()
        self._headers(status)
        self.wfile.write(payload)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        try:
            if parsed.path == "/api/status":
                self.send_json({
                    "service": "mend-ais-public-demo",
                    "status": "PASS",
                    "services": probe_services(),
                    "dataset_sha256": sha256_obj(load_json(DATASET)),
                    "fcg_sha256": hashlib.sha256(FCG.read_bytes()).hexdigest(),
                })
            elif parsed.path == "/api/fcg":
                self.send_json(load_json(FCG))
            elif parsed.path == "/api/dataset":
                self.send_json(load_json(DATASET))
            elif parsed.path == "/api/demo":
                purpose = urllib.parse.parse_qs(parsed.query).get("purpose", ["research"])[0]
                self.send_json(demo(purpose))
            elif parsed.path in {"/", "/index.html"}:
                payload = (WEB / "index.html").read_bytes()
                self._headers(200, "text/html; charset=utf-8")
                self.wfile.write(payload)
            elif parsed.path == "/sdk/mend-sdk.js":
                payload = (ROOT / "sdk/js/mend-sdk.js").read_bytes()
                self._headers(200, "text/javascript; charset=utf-8")
                self.wfile.write(payload)
            else:
                self.send_json({"error": "not_found", "path": parsed.path}, 404)
        except ValueError as exc:
            self.send_json({"error": str(exc)}, 400)
        except Exception as exc:
            self.send_json({"error": type(exc).__name__, "detail": str(exc)}, 500)

    def log_message(self, fmt, *args):
        print("[mend]", fmt % args)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8899)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Mend AIs demo listening on http://{args.host}:{args.port}")
    server.serve_forever()

if __name__ == "__main__":
    main()
