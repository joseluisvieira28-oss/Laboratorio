# POS-UNBONDING-COMPLETION-SUPPLY-RELEASE-001 — SOURCE GATE CLOSEOUT V0.3

Date: 2026-10-07  
Branch: `pos-unbonding-completion-001-source-remediation-v0.3-raw-block-2026-10-07`  
Freeze commit: `93e0c6abff72d1d645c709382d8f06ccc558a34e`  
Qualification commit: `0edbd9b83d46a4521106823315175a410c2bfdd6`  
Main baseline verified unchanged: `f263c6c6f3a57f26666a7aee28e782f2cbd08418`

## Final V0.3 verdict

**SOURCE_HISTORICAL_COVERAGE_BLOCKED**

This is a source/data verdict only.

- `SOURCE_GATE_PASS`: NO
- `NO_EDGE`: NOT TESTED / NOT APPLICABLE
- Market outcomes opened: NO
- Development run: NO
- 2025/2026 outcomes opened: NO
- Live trading/orders/account/private exchange activity: NO
- main changed: NO

## Why V0.3 does not pass

V0.3 successfully proved that a known historical staking cohort can be reconstructed and verified from raw canonical blocks without relying on `tx_search`. It also materially improved independent archive coverage:

- ATOM: two-source fixed-height reconciliation already proven in V0.2.
- OSMO: two-source fixed-height reconciliation already proven in V0.2.
- TIA: new two-source fixed-height reconciliation proven (KJNodes + Numia).
- DYDX: new two-source fixed-height reconciliation proven (Kingnodes + Polkachu).
- KAVA: Kava Labs historical archive works, but no independent second historical path was proven.

However, the frozen source gate is not a collection of isolated fixed-height demonstrations. It requires a complete and independently reconcilable 2023-2024 census from which material completion chain-days can be measured.

The public historical transaction-index routes tested in V0.3 do not provide that census:

- archive `block_search` / `tx_search` is unavailable on the tested archival operators;
- ordinary public RPC indexes either return no historical matches in bounded historical windows or require an exact already-known height;
- Cosmos SDK REST transaction search, tested with both legacy `events=` and v0.50+ `query=` forms, likewise provides no bounded historical undelegation rows on the tested providers;
- raw block access is available for several chains and validates known heights, but no complete bounded public index/export was identified that can enumerate every qualifying initiation/completion across the frozen two-year interval.

Therefore:
- lifecycle reconstruction primitive = PROVEN;
- complete census discovery = NOT PROVEN;
- cancellation/slash/hold reconciliation at census scale = NOT PROVEN;
- `>=40` material chain-days TOTAL across `>=5` chains = UNKNOWN;
- the 10 bp materiality threshold remains frozen but has not been applied to a complete census;
- the source gate cannot legitimately advance to market-data values or PRE-OUTCOME analysis.

## Scientific interpretation

This closeout does **not** imply that unbonding completion has no economic effect.

No token price, benchmark price, return, volume, PnL or economic outcome was examined. Consequently the economic hypothesis remains **untested**.

The useful scientific result of V0.3 is narrower:

> Native Cosmos x/staking completion is a reconstructible causal primitive at known canonical heights, but the present public/no-auth historical source stack is insufficient to prove a complete multi-chain 2023-2024 census under the frozen standards.

## Reopening rule

Do not reopen this version by:
- lowering the 10 bp materiality threshold;
- reducing the >=40 TOTAL / >=5-chain bar;
- replacing failed chains based on outcomes;
- using vote/expected maturity timestamps instead of actual completion;
- treating random raw-block samples as a complete census;
- opening prices first and repairing the source set afterward.

A future source-remediation version may reopen only upon a **genuinely new pre-outcome source capability**, such as:
- a public/free historical transaction index that retains the full frozen interval;
- an independently verifiable bulk historical block/transaction export;
- a chain-native historical dataset/API that enumerates staking initiations and cancellations with complete pagination;
- an equivalent reproducible source that makes exhaustive census discovery tractable before any market outcome is opened.

Any such reopening must preserve V0.3 as immutable evidence and freeze any new source-selection rule before census/outcome access.

## Final disposition

**PARKED — SOURCE HISTORICAL COVERAGE BLOCKED.**

No PRE-OUTCOME freeze is created.  
No Development test is authorized.  
No market outcomes are to be opened for this family from V0.3.
