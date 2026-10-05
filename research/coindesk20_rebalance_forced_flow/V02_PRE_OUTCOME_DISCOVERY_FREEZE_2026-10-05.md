# COINDESK20-REBALANCE-FORCED-FLOW-001 — V0.2 PRE-OUTCOME DISCOVERY FREEZE
Date: 2026-10-05
Status: FROZEN BEFORE ANY 2024-2025 EVENT-WINDOW MARKET PRICE INSPECTION

## Authority
V0.1 SOURCE_GATE_PASS established:
- seven complete post-launch quarterly reconstitutions through 2025-10;
- 14 asset-level ADD/DELETE observations;
- 14/14 publication-before-implementation;
- no event-window outcomes opened.

## Economic hypothesis
Publicly announced CoinDesk 20 constituent changes may induce anticipatory tracking/rehedging flow before the official implementation boundary.

Direction is fixed ex ante:
- ADD -> LONG sign (+1)
- DELETE -> SHORT sign (-1)

This is a discovery test of a signed information/flow effect, NOT yet a tradability claim.

## Fixed development universe
All 14 V0.1 source-census changes:
2024-04: ADD NEAR; DELETE XLM
2024-07: ADD HBAR, RNDR; DELETE DOGE, SHIB
2024-10: ADD XLM; DELETE ATOM
2025-01: ADD SUI, AAVE; DELETE RENDER, ETC
2025-10: ADD CRO; DELETE FIL

2025-04 and 2025-07 have no constituent changes and produce no asset-level observation.

No changed asset may be removed due to later outcome.

## Market source
Primary and ONLY V0.2 market venue:
Binance SPOT public historical archive, USDT pair.

BTC benchmark:
BTCUSDT on the same source and exact timestamps.

No runtime venue shopping and no fallback venue in V0.2.

An observation is market-valid only if the required asset and BTC bars exist at all frozen boundaries.

If fewer than 12 of 14 observations are market-valid:
SOURCE_BLOCKED.

## Conservative publication boundary
The source corpus proves publication calendar dates but not a defensible common intraday publication timestamp.

Therefore primary entry time is deliberately late:
T_entry = 00:00:00 UTC exactly TWO calendar days after the official publication date.

Entry price:
OPEN of the 1-minute bar at T_entry.

This boundary is fixed to prevent look-ahead from ambiguous publication timing.

## Implementation boundary
Official implementation is 16:00 America/New_York on the stated implementation date.

Primary exit:
the CLOSE of the final complete 1-minute bar ending at or before T_implementation - 5 minutes.

The five-minute pre-implementation buffer avoids assuming the strategy can transact exactly on the official rebalance print.

## Primary outcome
For each observation:
R_asset = exit / entry - 1
R_btc = BTC exit / BTC entry - 1
R_exbtc = R_asset - R_btc

Signed outcomes:
SIGNED_RAW = direction * R_asset
SIGNED_EXBTC = direction * R_exbtc

Primary endpoint:
median SIGNED_EXBTC.

## Primary discovery gate — ALL required
- n_market_valid >= 12
- median SIGNED_EXBTC > +1.00%
- SIGNED_EXBTC positive hit rate >= 65%
- median SIGNED_RAW > 0
- leave-one-observation-out median SIGNED_EXBTC > 0 for every omission
- leave-one-QUARTER-out median SIGNED_EXBTC > 0 for every changed quarter omitted
- no single observation contributes >35% of summed positive SIGNED_EXBTC
- median ADD R_exbtc > 0
- median (-DELETE R_exbtc) > 0

If all pass:
SURVIVES_FORCED_FLOW_DISCOVERY

If source valid but any primary gate fails:
NO_EDGE_DISCOVERY

## Secondary diagnostics — NON-GATING
- entry at +24h rather than +48h;
- exit T_impl - 60m;
- exit T_impl + 5m;
- raw asset return;
- BTC-relative return;
- MFE/MAE between primary entry/exit;
- quarter-level equal-weight signed portfolio return;
- result by ADD versus DELETE.

Secondary diagnostics cannot rescue the primary gate.

## Cluster integrity
Multiple asset changes sharing one quarterly announcement are not independent events.

Therefore:
- report quarter clusters explicitly;
- leave-one-quarter-out robustness is mandatory;
- do not report naive t-test significance as decisive evidence.

## Costs / tradability
V0.2 does NOT claim executable edge.
No fee/slippage/borrow/funding model is applied to the primary scientific discovery endpoint.

If V0.2 survives, a separate pre-outcome EXECUTION FREEZE must be created before any confirmatory period is opened. It must specify instrument, long/short implementation, borrow/funding, spread/slippage, fees, capacity, entry/exit mechanics and later holdout.

## Holdout governance
2026 price outcomes remain CLOSED for this family.
2026 may not be opened to rescue or tune V0.2.
Because 2026 contains only a limited number of quarterly reconstitutions, a later confirmatory protocol may need additional forward quarters rather than lowering sample gates.

## Anti-hindsight
After this freeze:
- no changing ADD/DELETE direction;
- no changing +48h primary entry;
- no changing -5m primary exit;
- no changing +1% median gate;
- no lowering 65% hit rate;
- no removing losing assets or quarters;
- no adding fallback venues based on outcomes;
- no changing BTC-relative formula;
- no post-outcome tuning presented as confirmatory.

## Governance
Research-only.
Public data only.
No main merge.
No live trading/orders.
No accounts/wallets/private endpoints.
No exchange mutation.
