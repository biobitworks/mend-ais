# Mend FCO/FCG Bedrock successor

Navigation begins at `breakpoints/bp8_mend_public_successor_merkle_v1.json`, then `agent_manifest_successor.json`, then `fcg/successor_fcg.json`. Local credentials remain outside the repository.

Run `python3 scripts/verify_successor.py` to verify all nine sequential checkpoint roots, FCO identities, graph references, pre-result routing custody, and the fixture-specific egress result.

Run `python3 successor_server.py` and open `http://127.0.0.1:8900/` for the judge surface. The API exposes `/api/breakpoint`, `/api/fcg`, `/api/fcos`, `/api/fco/<id>`, `/api/traversal/<release_fco_id>`, and `/api/status`.

The observed Bedrock result is probabilistic evidence. Antigence performs bounded anomaly/challenge verification. Neither controls disclosure; `MEND_SYNTHETIC_RESEARCH_RELEASE_V1` is the deterministic release authority.
