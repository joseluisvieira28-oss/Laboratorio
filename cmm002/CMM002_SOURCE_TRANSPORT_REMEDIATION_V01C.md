# CMM-002 — SOURCE TRANSPORT REMEDIATION V0.1C

Status: FROZEN BEFORE ANY CMM-002 2025 BTC OUTCOME ACCESS

V0.1B successfully reached the Wayback availability/replay path but the archived payload was returned as raw gzip bytes. The runner attempted direct UTF-8 decoding and failed with UnicodeDecodeError before parsing any stablecoin row or computing any outcome.

V0.1C changes ONLY transport decoding:
- same target URL;
- same Wayback availability endpoint;
- same <= 2025-12-31 boundary;
- same resolved archived snapshot semantics;
- if replay bytes begin with gzip magic 1f8b, decompress once before JSON decode;
- record SHA256 of both transport bytes and decoded payload;
- preserve every V0.1A/V0.1B semantic-continuity and no-2026 gate unchanged.

No market outcome, PnL, event return, threshold, component, cost, direction or period changes.
2025 BTC outcomes remain closed during this gate.
2026 remains forbidden.
