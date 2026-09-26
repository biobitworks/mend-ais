# AGENTS.md

## Public downstream-agent contract

Start with `agent_manifest.json` and `fcg/core_fcg.json`.

### Required sequence

1. Verify `receipts/public_release_receipt.json` against the published files.
2. Read the FCG and preserve every node's explicit state.
3. Run `./scripts/status.sh`; do not upgrade DEGRADED or NOT_TESTED states.
4. Run `./scripts/smoke.sh` before treating the Mac demo lane as live.
5. Use `GET /api/demo?purpose=research` for the privacy/minimization demonstration.
6. Treat `model_advisory` as probabilistic evidence only.
7. Treat `release` as deterministic policy output for the supplied synthetic fixture only.

### State discipline

`PROPOSED ≠ IMPLEMENTED ≠ EXECUTED ≠ OBSERVED ≠ SUPPORTED`.

Preserve `FAILED`, `NULL`, `NEGATIVE`, `DEFERRED`, `NOT_TESTED`, `UNKNOWN`, and `NOT_COMPUTED`.

### Security boundary

Do not ingest real PHI into this public demo. The supplied data is synthetic.
Do not infer HIPAA compliance, formal de-identification, clinical correctness, or medical-device readiness from a passing smoke test.
