# INDEX-CROSSVENUE-001 — FORMAL AUTHORITY CLOSEOUT

Date: 2026-10-05
Branch: `index-crossvenue-001-authority-reconciliation-2026-10-05`
Status: CLOSED

## Scope

This closeout formalizes the authority reconciliation already committed on this branch.
No new market outcomes were opened. No parameters were changed. No private endpoints,
account reads, wallets, orders, exchange mutation, or live trading were used.

## Core finding

`INDEX-CROSSVENUE-001` is not a canonical pre-existing scientific family ID in the audited
repository history. The previously quoted result of 143 event baskets / 17 dates /
+20.0820 bps gross / +4.0820 bps after 16 bps does NOT belong to an index cross-venue family.

That result belongs to the distinct equity/ETF overshoot family using individual stock/ETF
perpetual mappings across MEXC and Binance/Bitget. It must not be transferred to NAS100,
SP500, or any synthetic index interpretation.

## Canonical external index cross-venue verdicts

### NAS100
Family: `MEXC-HL-NAS100-DISLOCATION-001`

Frozen V0.7 discovery:
- 16 cells
- N = 0 in every cell
- minimum frozen dislocation threshold = 10 bps
- no retrospective OOS opened

Canonical verdict:
`NO_NAS100_CROSSVENUE_OOS_SURVIVOR_AT_FROZEN_V07_GATE`

### SP500
Family: `MEXC-HL-SP500-LEADLAG-001`

Frozen V0.4 discovery:
- 36 cells
- widest family produced only 4 non-overlapping events
- pre-Holm eligible cells = 0
- Holm-selected cells = 0

Canonical verdict:
`NO_EDGE_AT_FROZEN_V04_GATE`

## Separate index mechanism that DID survive

Family: `GLOBAL-ASSET-SP500-BASIS-001`

This is NOT external cross-venue. It is MEXC traded contract versus MEXC index convergence.

Untouched September holdout:
- N = 654
- win rate = 54.4342507645%
- mean gross signed return = +0.5177567737 bps
- one-sided exact p = 0.0128735220
- both chronological halves positive

Scientific verdict:
`REPLICATED_SIGNAL_SURVIVOR`

Execution verdict for the standard published MEXC API fee route:
`EXECUTION_FEE_BLOCKED_STANDARD_API`

The measured gross edge is approximately +0.5178 bps, far below the standard published
API fee-only round-trip hurdle documented by the existing execution-feasibility gate.

## Final verdict for the user task label

`INDEX-CROSSVENUE-001`:
`CLOSED_AS_MISATTRIBUTED_LABEL__NO_CANONICAL_INDEX_CROSSVENUE_SURVIVOR`

This is not a post-hoc scientific NO_EDGE result for a newly invented family. It is an
authority/governance closeout proving that the apparent survivor was attributed to the
wrong economic family and that the two canonical external index cross-venue families
already failed their frozen gates.

## What remains legitimate

A future true index cross-venue continuation is allowed only as a NEW family with:
1. explicit public/free source binding;
2. a committed pre-outcome rule and activation freeze;
3. untouched future data after that freeze;
4. no inheritance of the equity/ETF overshoot economics;
5. no lowering of NAS100/SP500 historical gates to rescue prior failures.

No merge to main is authorized by this closeout.
