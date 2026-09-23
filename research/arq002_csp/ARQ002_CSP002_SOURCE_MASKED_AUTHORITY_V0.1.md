# ARQ-002-CSP-002 — SOURCE-MASKED DISCOVERY AUTHORITY V0.1

Date: 2026-09-23
Branch: `arq002-cvd-sweep-positioning-v0.2`
State: FROZEN_PRE_OUTCOME / RESEARCH_ONLY / ECONOMIC_OUTCOMES_UNOPENED

## Lineage

Parent archaeology hit:
ARQ-002 — CVD + Liquidity Sweeps + Positioning Confirmation.

Immediate predecessor:
ARQ-002-CSP-001.

CSP-001 is CLOSED as SOURCE_DATA_INSUFFICIENT because its source contract required 288/288 Binance metrics timestamps on every 2024 UTC day.

No CSP-001 economic values, CVD values, OI values, funding values, sweep returns or PnL were opened before that closeout.

CSP-002 is a NEW prospective source-resilient child. It does not reinterpret CSP-001 as passing.

## Why a new child is admissible

Source-only census established, before economic outcomes:
- 2024-02-16 has 163/288 metrics timestamps; missing suffix 13:35–23:55 UTC.
- 2024-10-28 has 286/288 metrics timestamps; missing 16:25–16:30 UTC.
- all observed metrics timestamps remain exactly on the 5-minute grid;
- zero conflicting duplicate groups were found;
- ten other monthly source shards passed the strict CSP-001 gate.

CSP-002 therefore freezes a source-availability mask before any economic values are opened.

## Scientific contract

Except for the source-mask policy below, the economic experiment is IDENTICAL to:
`research/arq002_csp/ARQ002_CSP_DISCOVERY_AUTHORITY_V0.1.md`

Inherited unchanged:
- asset: BTCUSDT USD-M perpetual only;
- price sweep/reclaim proxy;
- 30-minute prior high/low reference;
- strict breach + close-back-inside semantics;
- ambiguous both-side minutes excluded;
- event-minute aggTrades CVD ratio;
- CVD sign confirmation;
- exact adjacent 5-minute OI increase confirmation;
- latest causal funding sign confirmation;
- A/B/C/D ablation;
- REVERSAL direction;
- entry at next 1m open;
- five-complete-minute outcome;
- LOW10 / BASE14 / STRESS20 costs;
- UTC-day block bootstrap, 10,000 reps, seed 2002001;
- every Discovery gate and robustness rule;
- 2024 Discovery only;
- 2025 locked;
- 2026 forbidden.

No scientific threshold or direction changes.

## Frozen source-mask rule

For each UTC calendar day D in 2024:

A day is SOURCE_ELIGIBLE only if ALL are true:
1. checksum-verified BTCUSDT daily aggTrades object exists and passes structural identity/timestamp checks;
2. checksum-verified BTCUSDT 1m kline object contains the exact 1,440-minute UTC grid;
3. checksum-verified BTCUSDT metrics object contains the exact 288 unique 5-minute UTC timestamps after collapse of exact-identical duplicate rows only;
4. zero conflicting metrics duplicate group;
5. relevant funding archive is checksum-verified and causal funding state is available under the frozen event rule.

If any daily condition fails:
- the ENTIRE UTC day is SOURCE_MASKED;
- no sweep event is constructed on that date;
- no CVD/OI/funding economic value for that date is admitted to Discovery;
- no return/outcome for that date is computed;
- no interpolation, forward fill, partial-day salvage or alternate provider.

## Annual source adequacy

Before outcomes, the full source census must establish:
- >=99.0% of the 366 UTC days in 2024 are SOURCE_ELIGIBLE;
- therefore at least 363 complete days;
- every masked day is listed and frozen before economic analysis;
- no masked day may be restored after outcomes.

Known source-only candidate mask from CSP-001 diagnostics:
- 2024-02-16
- 2024-10-28

This list is not accepted merely by assumption. CSP-002 must complete the previously unscanned portions of February and October and persist a canonical annual source receipt.

## Boundary adjacency

Events on a SOURCE_ELIGIBLE day still require all event-level causal inputs.

If the previous required OI row lies on a masked day or is unavailable:
- the event is ineligible.

No cross-gap OI comparison.

## Discovery gates

All twelve gates in CSP-001 remain binding, including:
- D-confirmed N >=200;
- >=60 unique UTC days;
- BASE14 >0;
- STRESS20 >0;
- confirmed-minus-rejected >0;
- bootstrap lower95 >0;
- both sweep directions positive;
- >=7/12 positive calendar-month means;
- top-1% removal positive;
- max month concentration <=25%.

Masked days do not count as positive months or negative months; monthly mean is defined on eligible observations in that month. A calendar month with zero D-confirmed observations remains non-positive exactly as CSP-001 froze.

## Source-stage terminal states

- SOURCE_MASK_PASS
- SOURCE_DATA_INSUFFICIENT
- SOURCE_PROVENANCE_FAIL
- TECHNICAL_FAIL_CLOSED

## Economic terminal states

- DISCOVERY_SURVIVES_NOT_EDGE
- DISCOVERY_FAIL_NO_PROMOTION

## No-rescue boundary

After any 2024 economic outcome is opened, do not:
- change the 99.0% source threshold;
- unmask a failed day;
- partially salvage a masked day;
- alter event rules, CVD/OI/funding semantics, costs, direction, horizon, bootstrap or gates;
- open 2025 after Discovery failure.

## Governance

No live trading.
No orders.
No wallets.
No exchange mutation.
No main merge.
No deployment.
