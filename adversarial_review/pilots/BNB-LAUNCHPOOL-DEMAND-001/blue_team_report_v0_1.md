# BNB-LAUNCHPOOL-DEMAND-001 — BLUE TEAM REPORT V0.1

**Phase:** Historical + governance reconstruction before final prospective Diamond adjudication  
**Blue verdict:** **PASS — HISTORICAL EVIDENCE RECONSTRUCTED / FINAL DIAMOND NOT YET ADJUDICABLE**

## Freeze reconstruction

Controlling lineage reconciled:

- Promotion Policy V3: `ND-PROMOTION-POLICY-V3.0-FROZEN`.
- V3 re-adjudication closeout blob: `1c010dca02a84c21a2d9d2a48e7dabf8d5c1be83`.
- Parent forward freeze commit: `34d35904bc097bd3ab5c420f97f0c12c62a802f8`, created 2026-09-16T20:51:23Z.
- Diamond V0.2 freeze head: `083b7196b0c064622182a3f1ed087b1082168428`.
- Canonical measurement-sidecar commit: `8346c0716edd661e13b063276bfe13bb5e08b955`.

Frozen parent science remains LONG BNBBTC, first 15m open strictly after the canonical eligible Launchpool announcement, 24h hold, BASE20/STRESS30, one active trade, <=60m clustering, no stop/target/leverage.

## Evidence reconstruction

Three immutable historical blocks were independently read from their ledgers and summary artefacts:

| Block | N | BASE20 mean bps | BASE20 PF | Known issue |
|---|---:|---:|---:|---|
| Pre-Discovery projects 1–30 | 27 | +76.8526 | 1.3921 | concentration 48.01%; 2020 negative / 2021 dominant |
| Discovery 2022–2024 | 31 | +88.8665 | 2.2104 | frozen bootstrap lower bound < 0 |
| Independent 2025 OOS | 8 | +57.6174 | 2.5478 | concentration 53.96%; small N |

Pooled descriptive evidence, already opened before this review: N=66, BASE20 mean +80.1639 bps/trade, PF 1.6727.

The audit independently recomputed the pooled ledger from the three immutable ledgers and matched the published pooled metrics.

## Blue checks

- **BT-001 Freeze reconstruction: PASS.**
- **BT-002 Source provenance: PASS.** Official Binance announcement source; canonical publication timestamps; provider/checksum-bound Binance Data Vision market archives in the historical runs.
- **BT-003 Exact replication: PASS for ledger-level arithmetic.** The three ledgers reproduce published BASE20 means/PFs and pooled metrics.
- **BT-004 Cost model: PASS.** Frozen BASE20/STRESS30 preserved. Additional adversarial repricing at 40 and 60 bps does not alter candidate rules.
- **BT-005 OOS/holdout compliance: PASS.** Discovery blocked 2025/2026; independent 2025 OOS remained isolated; pre-Discovery path excluded later years; 2026 forward boundary remains protected.
- **BT-006 Regime coverage: PASS WITH MATERIAL FRAGILITY.** Positive aggregate blocks, but year dispersion is large.
- **BT-007 Concentration: MATERIAL FRAGILITY.** Two independent small blocks exceeded the old 40% within-block concentration gate.
- **BT-008 Execution feasibility: INCOMPLETE FOR CAPITAL.** Historical fixed-cost modelling exists; trade-size/depth/slippage proof is not sufficient to infer live capacity.
- **BT-009 Forward integrity: PASS AT ARCHITECTURE LEVEL.** Strict post-freeze boundary, no backfill, first-25 immutability and sidecar isolation are explicit. Final prospective evidence remains outstanding.
- **BT-010 Evidence chain: PASS.** Hashes/commits/ledger fingerprints are present across the lineage.

## Blue conclusion

The positive historical effect is reproducible from the preserved ledgers and survives severe cost repricing. The current evidence supports keeping the existing V3 Tier-2 / Quase-Diamante classification as historical state.

Blue does **not** claim Diamond survival, Tier 1, micro-live readiness or capital authority. The prospective Diamond V0.2 gate remains controlling.
