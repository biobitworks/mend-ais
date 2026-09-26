# Mend AIs

**Local-first health data mesh — public hackathon judge MVP**

Mend AIs demonstrates a narrow, auditable primitive: synthetic health data is processed inside a local Mac Studio boundary, a real local Liquid model can produce an advisory interpretation, and a deterministic purpose gate controls the released object.

> **Claim boundary:** local execution reduces network exposure; it does not by itself establish HIPAA/GDPR/CCPA compliance or formal de-identification. The current public demo contains synthetic data only.

## 60-second judge start

```bash
git clone https://github.com/biobitworks/mend-ais.git
cd mend-ais
./scripts/start_macstudio.sh
./scripts/smoke.sh
```

Then open **http://127.0.0.1:8899** on the Mac. The startup script also prints the LAN URL for a phone on the same network.

## Core resource matrix

| Layer | Selected core | Current evidence |
|---|---|---|
| Dataset | `synthetic_fhir_bundle.json` | **IMPLEMENTED**; synthetic; SHA-256 pinned in FCG |
| Core model | Liquid LFM2 230M Q4_K_M | **OBSERVED_EXECUTED** through Ollama |
| Model runtime | Ollama 0.33.0 | **OBSERVED_PASS** on Studio |
| Orchestration | Ollarma | **OBSERVED_DEGRADED_CHAT_PASS**; direct model chat works, selection artifact stale |
| Release authority | deterministic Mend gate | **IMPLEMENTED**; model is advisory only |
| Mac SDK | Python `MendClient` | **IMPLEMENTED_COMPILE_PASS** |
| S26 SDK | zero-install browser `MendClient` | **IMPLEMENTED_SYNTAX_PASS / NOT_TESTED_ON_S26** |
| FCG | `fcg/core_fcg.json` | **IMPLEMENTED** with explicit evidence states |
| Antigence | private existing project | source built; runtime currently degraded, not a live MVP dependency |
| SeedGraph | private existing project | CLI PASS; graph backend not running |
| GettingScienceDone | private existing project | CLI PASS; doctor degraded by skill-install drift |

## What the live demo proves

| Demo observation | Status |
|---|---|
| Local installed Liquid model is addressable | OBSERVED |
| Local Ollarma route can call that model | OBSERVED |
| Synthetic dataset has a pinned content hash | SUPPORTED |
| Research release is produced by deterministic policy | IMPLEMENTED |
| Explicit identifiers are absent from research release fixture | TESTED BY `smoke.sh` |
| Model controls release | **NO** — intentionally false |
| Native S26 inference | NOT_TESTED |
| HIPAA compliance / formal de-identification | NOT_ESTABLISHED |

## FCG: fastest way to understand the stack

Open **[`fcg/core_fcg.json`](fcg/core_fcg.json)** first. It links the core dataset, model, runtimes, SDKs, devices, policy gate and verification check. Every node carries a state such as `OBSERVED_PASS`, `DEGRADED`, or `NOT_TESTED`.

Run:

```bash
python3 scripts/verify_fcg.py
```

This validates graph references and the exact dataset SHA-256. It deliberately does **not** claim a Merkle root.

## Judge navigation

| Path | Why it matters |
|---|---|
| [Judge navigation](docs/JUDGE_NAVIGATION.md) | shortest inspection path for humans and agents |
| [Architecture](docs/ARCHITECTURE.md) | trust boundary and private/public separation |
| [Core FCG](fcg/core_fcg.json) | machine-readable system map |
| [Synthetic core dataset](data/core/synthetic_fhir_bundle.json) | inspect exactly what enters the demo |
| [Python SDK](sdk/python/mend_sdk.py) | Mac/downstream-agent integration |
| [Browser SDK](sdk/js/mend-sdk.js) | S26/browser integration |
| [Studio audit](receipts/studio_resource_audit_20260926.json) | exact observed local state |
| [Release receipt](receipts/public_release_receipt.json) | exact public-file hashes and computed release root |

## API

Once running:

| Endpoint | Purpose |
|---|---|
| `GET /api/status` | live Ollama/Ollarma/core-model probes |
| `GET /api/fcg` | machine-readable FCG |
| `GET /api/dataset` | synthetic input |
| `GET /api/demo?purpose=research` | minimized research release + egress scan |
| `GET /api/demo?purpose=treatment` | synthetic treatment-purpose release |

## S26 / phone demo

Connect the S26+ to the same LAN as the Studio, run `./scripts/start_macstudio.sh`, and open the printed `LAN http://...` address in Chrome. The browser uses the same public JavaScript SDK in `sdk/js/mend-sdk.js`.

**Current evidence state:** browser SDK implemented; actual S26 execution is NOT_TESTED in this release receipt because this session has no connected Android/ADB target.

## Private platform boundary

Antigence, Ollarma, SeedGraph, and GettingScienceDone are existing private projects. This public repository does not copy their private source. It exposes only a public integration contract and exact observed states needed for the demo.

## Safety

This is a research/hackathon demonstrator, not a medical device and not a clinical decision-support system. It uses synthetic data and does not make diagnosis or treatment decisions.
