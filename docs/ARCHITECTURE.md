# Mend AIs — Public MVP Architecture

## Trust boundary

```text
Synthetic health record
        |
        v
Mend local bridge on Mac edge node
        |----> Liquid LFM2 advisory inference via Ollarma/Ollama
        |
        v
Deterministic purpose gate
        |
        v
Explicit-identifier egress scan
        |
        v
Purpose-bound release object + SHA-256 receipt
```

The model is **not** the release authority. Its output is shown separately as advisory model evidence.

## Existing private platform projects

The public MVP interoperates with, but does not publish, the private implementations of:

| Project | Role | Observed state on Studio |
|---|---|---|
| Antigence | deterministic/AIS verification layer | source present; runtime degraded by broken external-volume venv symlink |
| Ollarma | bounded local-model execution | service live on 127.0.0.1:8484; direct chat works; selection state degraded/stale |
| SeedGraph | provenance/evidence graph | CLI 0.1.0 runs; graph container not running |
| gsigmad | governed science execution | CLI 1.3.0b2 runs; doctor reports skill-install drift |

The live judge path therefore depends only on Ollama, the installed Liquid model, Python 3, and this public repository.

## Mobile boundary

The S26+ surface is the zero-install browser SDK served by the Mac edge node. It is suitable for LAN demonstration. Native Android/NPU inference is a successor lane and is explicitly **NOT_TESTED** in the current receipt because no Android SDK/ADB-connected device was available in this execution turn.

## Security scope

This repository contains synthetic data only. Passing the explicit-identifier egress check demonstrates this implementation's policy behavior for the supplied fixture; it is not evidence of HIPAA compliance, formal de-identification, clinical validity, or universal privacy.

## Breakpoint-bound local capability layer

Public identity is anchored by `MEND_CORE_CAPABILITY_MERKLE_V1`, not by machine names. The breakpoint hashes the declared core dataset, FCG, SDKs, demo server, receipts, and judge documentation.

A local edge node may have `~/.config/mend-ais/unlock.json`. That descriptor is intentionally outside Git and is mode 0600. It binds local resources to one exact public breakpoint root.

A downstream agent therefore follows: verify breakpoint → inspect FCG → request local capability → execute bounded action. Moving the repository to another machine does not move private capability metadata with it.
