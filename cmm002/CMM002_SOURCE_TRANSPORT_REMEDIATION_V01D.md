# CMM-002 — SOURCE TRANSPORT REMEDIATION V0.1D

Status: FROZEN BEFORE ANY CMM-002 2025 BTC OUTCOME ACCESS

V0.1C correctly identified the required gzip handling conceptually, but the generated Python source compared the replay prefix against the literal backslash characters "\\x1f\\x8b" rather than the binary gzip magic bytes 1f8b.

V0.1D is an implementation-only correction:
- replace that comparison with bytes.fromhex("1f8b");
- preserve the same Wayback snapshot discovery;
- preserve the same <=2025-12-31 boundary;
- preserve the same no-2026, schema, coverage and 2024 semantic-continuity gates;
- preserve all CMM-002 scientific rules unchanged.

No CMM-002 BTC outcome has been opened.
