# AGENTS.md

## Public downstream-agent contract

Start with `breakpoints/mend_core_breakpoint_v1.json`, then `agent_manifest.json` and `fcg/core_fcg.json`.

### Required sequence

1. Verify `breakpoints/mend_core_breakpoint_v1.json` with `python3 scripts/verify_breakpoint.py`.
2. Verify `receipts/public_release_receipt.json` against the published files.
3. Read the FCG and preserve every node's explicit state.
4. Run `./scripts/status.sh`; do not upgrade DEGRADED or NOT_TESTED states.
5. Run `./scripts/smoke.sh` before treating the Mac demo lane as live.
6. Use `GET /api/demo?purpose=research` for the privacy/minimization demonstration.
7. Treat `model_advisory` as probabilistic evidence only.
8. Treat `release` as deterministic policy output for the supplied synthetic fixture only.

### State discipline

`PROPOSED ≠ IMPLEMENTED ≠ EXECUTED ≠ OBSERVED ≠ SUPPORTED`.

Preserve `FAILED`, `NULL`, `NEGATIVE`, `DEFERRED`, `NOT_TESTED`, `UNKNOWN`, and `NOT_COMPUTED`.

### Security boundary

Do not ingest real PHI into this public demo. The supplied data is synthetic.
Do not infer HIPAA compliance, formal de-identification, clinical correctness, or medical-device readiness from a passing smoke test.
