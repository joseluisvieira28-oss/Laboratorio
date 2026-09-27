# ETH-STAKING-FLOW-001 — V3 STAGE-A CBT COVERAGE UNIT CORRECTION V0.2.1A

Date frozen: 2026-09-27
Status: FROZEN BEFORE CORRECTED NETWORK EXECUTION / SOURCE-METADATA ONLY

## Reason

V0.2.1 incorrectly supplied raw Ethereum slot numbers to the CBT coverage API.

The official CBT implementation shows that for interval type `slot`, processed
positions are Unix timestamps. The official examples query slot_start_date_time
using `fromUnixTimestamp({{ .bounds.start }})`, and incremental tests identify
task start as a Unix timestamp.

The V0.2.1 response independently confirmed this scale: processed positions were
approximately 1.78e9, not Ethereum slot numbers.

Therefore V0.2.1 `CBT_COVERAGE_TARGETS_FAIL` is a technical unit mismatch and
MUST NOT be interpreted scientifically.

## Corrected frozen positions

Use the already-frozen first-epoch-at-or-after-midnight timestamp:
`target_unix = 1606824023 + target_epoch * 384`.

Controls:
- 2025-02-24: epoch 347738 => 1740355415
- 2025-03-02: epoch 349088 => 1740873815
- 2025-10-17: epoch 400613 => 1760659415

Missing:
- 2025-02-25: 347963 => 1740441815
- 2025-02-26: 348188 => 1740528215
- 2025-02-27: 348413 => 1740614615
- 2025-02-28: 348638 => 1740701015
- 2025-03-01: 348863 => 1740787415
- 2025-10-18: 400838 => 1760745815
- 2025-10-19: 401063 => 1760832215

Full frozen source endpoints:
- 2025-01-01 epoch 335588 => 1735689815
- 2026-08-31 epoch 472163 => 1788134615

## Endpoint and decision rules

Same official public CBT management endpoints as V0.2.1.

PASS only if all ten exact corrected timestamps are inside processed coverage
and the debug endpoint reports model coverage complete/non-blocking at each.

FAIL only if corrected timestamps are explicitly outside/gapped.

Any schema ambiguity => metadata inconclusive.

A PASS is source-coverage permission only, not Stage-A source pass and not
permission to open market outcomes.

All V3 scientific rules and firewalls remain unchanged.
