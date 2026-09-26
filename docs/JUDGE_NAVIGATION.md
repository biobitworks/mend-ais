# Judge / Downstream Agent Navigation

| Need | Start here | Machine-readable? |
|---|---|---|
| Verify public core | `python3 scripts/verify_breakpoint.py` | Yes |
| Unlock local capabilities | `python3 scripts/unlock_local.py --list` | Yes |
| Run the demo | `./scripts/start_local.sh` | Yes |
| Verify live stack | `./scripts/smoke.sh` | Yes |
| Inspect resources/states | `fcg/core_fcg.json` | Yes |
| Inspect core dataset | `data/core/synthetic_fhir_bundle.json` | Yes |
| Call from Python | `sdk/python/mend_sdk.py` | Yes |
| Call from phone/browser | `sdk/js/mend-sdk.js` | Yes |
| Understand boundaries | `docs/ARCHITECTURE.md` | Markdown |
| Audit machine observations | `receipts/node_resource_audit_20260926.json` | Yes |
| Verify published artifact hashes | `receipts/public_release_receipt.json` | Yes after release sealing |

## Recommended downstream-agent sequence

1. Read `fcg/core_fcg.json`.
2. Reject any node whose state is `NOT_TESTED`, `DEGRADED`, or `UNKNOWN` when a PASS dependency is required.
3. Run `scripts/status.sh`.
4. Run `scripts/smoke.sh`.
5. Use `/api/demo?purpose=research` for the deterministic privacy demonstration.
6. Treat `model_advisory.text` as probabilistic output, never as release authorization.
7. Verify content hashes from the release receipt before relying on file identity.

No Merkle root should be inferred from the FCG itself unless a receipt explicitly declares its canonical leaves and computed root.

## Breakpoint-first agent entry

The stable public address is the Merkle breakpoint, not a machine hostname:

```bash
python3 scripts/verify_breakpoint.py
python3 scripts/unlock_local.py --list
```

`UNLOCKED` means the current machine has a local descriptor bound to the verified breakpoint. It does not mean a remote machine, private key, credential, or private repository has been published.
