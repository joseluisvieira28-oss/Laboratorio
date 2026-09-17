# CED-1D-V1 — V3 BYTE-EXACT SOURCE RECOVERY FREEZE — 2026-09-17

Status: `FROZEN_PRE_RECOVERY__SOURCE_ONLY__NO_OUTCOMES`

Policy: `ND-PROMOTION-POLICY-V3.0-FROZEN`

Purpose: recover the original CED 1D Discovery source bytes without changing the hypothesis, runner, universe, period, source rule or market outcomes.

## Historical state preserved

The historical CED-1D-V1 state remains `BLOCKED_BY_CANONICAL_WORKSPACE_BYTES_NOT_AVAILABLE_TO_EXECUTION_ENVIRONMENT`, not NO_EDGE and not Tier 4. Historical V1/V2 records are immutable.

Recovered runner package identity:

- package: `CED-1D-V1-DISCOVERY-CLOSEOUT-V0.2-MAPPED-V0.1.zip`
- ZIP SHA256: `d590b2fe3b86baa9b9b0c1e092cf53c6cb0067ebcafb9fd7a21002dd2df50841`
- ZIP bytes: 54,650
- tests: 69/69 PASS
- Python compile: PASS
- Windows validation: PASS
- clean extraction: PASS
- ZIP CRC: PASS
- receipt states 2025/2026 market data were not accessed and no market results/routing executed.

Recovered canonical workspace authority:

- workspace: `CED_PHASE2_WORKSPACE`
- canonical index: `REPAIR_A01/EVIDENCE/RESEARCH_INPUT_INDEX.json`
- observed index SHA256: `FB6DA37A934468D84EE95F4EAADB663900EB7B9687E4D3E34BC1579D20A2631B`
- dataset fingerprint: `0B3DE834CF5A126CB348596A466CE191E956640F4E7C3D8D3FBC8F38E1C5AD93`
- `dataset_manifest_R1.json` SHA256: `8E34D65B28CE9D908B85176728854A875927CDCD4DA7AE5EF0AC307555B15321`
- `phase2_dataset_evidence_R1.json` SHA256: `3730717187CC48A8E242CCE0D8D57BD74DF12ECD06B7C85D4B02D111A1A3A657`
- `dataset_fingerprint_preimage_R1.json` SHA256: `B0068DD708FCC957FDC7CF57288CD532DB902951E549F489251E692EDADD0E80`

Recovered `target_registry.json` contains per-month canonical identities including local SHA256, provider SHA256, provider checksum match, CRC, row counts and timestamp-integrity diagnostics.

## Frozen recovery universe

Exactly ten symbols:

- ADAUSDT
- AVAXUSDT
- BNBUSDT
- BTCUSDT
- DOGEUSDT
- ETHUSDT
- LINKUSDT
- LTCUSDT
- SOLUSDT
- XRPUSDT

Period: `2021-01` through `2024-12`, inclusive.

Expected source population: exactly 480 monthly Binance Spot 1m ZIP archives, plus the corresponding checksum authority. Historical console evidence records 960 files total for this period = 480 ZIP + 480 CHECKSUM, 240 files per year and 96 files per symbol.

2025: LOCKED / MUST NOT BE DOWNLOADED, OPENED OR USED BY THIS RECOVERY.

2026: LOCKED / MUST NOT BE DOWNLOADED, OPENED OR USED BY THIS RECOVERY.

## V3 source-recovery authority

This freeze prospectively authorizes provider re-download only as a **byte-exact source recovery operation**. It does not authorize source substitution.

A re-downloaded monthly archive qualifies as recovered canonical input only when all of the following are true:

1. the exact symbol/month exists in the historical `target_registry.json`;
2. the historical record is `status=PASS` and `classification=PASS`;
3. the historical record shows `provider_checksum_match=true`;
4. the newly downloaded provider checksum is valid;
5. the newly downloaded ZIP SHA256 equals the historical canonical `local_sha256`;
6. the newly downloaded ZIP SHA256 equals the historical canonical `provider_sha256`;
7. if historical `zip_sha256` is present, the new ZIP SHA256 equals it;
8. ZIP CRC passes;
9. no unexpected archive/member/path substitution occurs;
10. all 480/480 required Discovery archives satisfy these checks.

No tolerance, fallback, alternate mirror, recompressed archive, normalized CSV, generated replacement, partial corpus or majority-match rule is permitted.

A single unexplained byte mismatch means `BYTE_EXACT_RECOVERY_BLOCKED` and the CED candidate remains outside tiers / blocked.

## Registry binding gate

Before any provider download is used for scientific execution, the recovery runner must bind to a machine-readable, complete copy of the historical `target_registry.json` and verify that the filtered 2021-2024 population contains exactly 480 unique symbol/month records for the frozen ten-symbol universe.

The current ChatGPT execution environment can read the historical registry as indexed Library evidence, but cannot materialize its original raw bytes. Therefore **this document does not authorize reconstructing the registry manually from snippets or search output**. The complete machine-readable registry must be supplied/exported intact to the recovery runner before the 480-file recovery may be adjudicated PASS.

## Terminal classifications

- `BYTE_EXACT_RECOVERY_PASS`: 480/480 exact hash/authority matches plus runner/workspace preflight PASS.
- `BYTE_EXACT_RECOVERY_BLOCKED`: any missing registry binding, missing archive, mismatch, malformed checksum, CRC failure, path ambiguity or authority failure.
- Neither state is an economic verdict.

Only after `BYTE_EXACT_RECOVERY_PASS` may the already-existing frozen CED runner continue from its prior scientific gate. No redesign, parameter change or new hypothesis is permitted.

## Prohibitions

- no 2025 access;
- no 2026 access;
- no market outcome computation during byte recovery;
- no reconstructed/synthetic registry;
- no aggregated-output substitution;
- no parameter tuning;
- no cherry-picking;
- no source-rule relaxation after seeing mismatches;
- no live trading;
- no orders;
- no exchange mutation;
- no wallets;
- no alerts/webhooks;
- no merge to main.

This freeze is prospective relative to any new provider-byte recovery attempt under V3.
