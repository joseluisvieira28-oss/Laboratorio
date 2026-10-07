# COSMOS-NATIVE-EMISSION-PARAM-SHOCK-001 — PRE-OUTCOME ANALYSIS FREEZE V0.1

Date: 2026-10-07
Branch: cosmos-native-emission-param-shock-001-v0.1-preoutcome-2026-10-07
Parent source-gate commit: 7709c19a4476a5173d819d2ceb2d7a8b14a8fd43
Outcomes opened before this freeze: NO

## Scope

This freeze governs the one-shot Development test for the 12 source-frozen independent event-programs in SOURCE_GATE_RECEIPT_V01.md.

No event may be added, substituted or removed after market outcomes are opened except by a pre-existing fail-closed source/data rule. If a frozen event fails source eligibility before any market payload is fetched, the family loses the >=12-event source gate and Development does not run.

## Economic hypothesis

A binding reduction in native token issuance reduces the flow of newly created tokens received by validators/stakers/other recipients and therefore reduces structural potential sell supply.

Frozen directional hypothesis:
**effective issuance step-down -> positive subsequent token return relative to BTC.**

A null/negative result is accepted without sign switching.

## Event time

Primary event time T0:
**the first on-chain block / coordinated upgrade boundary at which the new lower effective issuance rule is actually in force.**

Not allowed as primary T0:
- forum post time;
- proposal submission time;
- vote start;
- arbitrary UTC day boundary;
- scheduled date if the actual chain activation differs.

For a pre-approved multi-step program such as INJ 3.0, the program contributes ONE observation. T0 is the first effective issuance reduction after program approval. Later scheduled reductions do not create new independent observations.

T_announce is frozen as a diagnostic timestamp only: the earliest timestamp at which the binding decision and its implementation schedule became publicly settled (normally governance passage or equivalent final ratification). T_announce cannot rescue a failed T0 primary.

## Dose

For each event:
D = (old effective annualized issuance rate - new effective annualized issuance rate) / old effective annualized issuance rate.

Use the actual effective issuance trajectory at T0, not merely nominal parameter ceilings.

If D cannot be reconstructed defensibly before price retrieval, the event fails source eligibility and the Development run is blocked.

## Market-data source rule

Primary instrument: liquid spot token market against USD/USDT.

Venue selection is mechanical and outcome-blind. Choose the first venue in this hierarchy that has continuous public hourly data covering at least T0-180d through T0+14d:

1. Binance spot USDT
2. Coinbase spot USD/USDT
3. Kraken spot USD
4. OKX spot USDT

Do not compare venue returns before choosing. No venue switching based on performance.

BTC benchmark uses the same venue where possible; otherwise Binance BTCUSDT.

If no allowed venue has the required continuous coverage for a frozen event, the event fails the pre-existing market-capability rule. Do not substitute another event.

## Entry and exit

Primary executable window:
- Entry: OPEN of the first complete 1-hour candle whose timestamp is >= T0.
- Exit: OPEN exactly 168 hours after the entry candle.
- Direction: LONG token, no leverage.

This prevents using a candle that partly precedes activation.

Primary gross abnormal return:
AR_7D = log(token_exit/token_entry) - log(BTC_exit/BTC_entry).

Primary fixed all-in execution cost:
40 basis points round trip.

Primary net abnormal return:
NET_AR_7D = AR_7D - 0.0040.

The fixed cost is deliberately conservative and is not tunable after outcomes.

## Diagnostics only — cannot rescue primary

Report, without changing verdict:
- 24h abnormal return;
- 72h abnormal return;
- 14d abnormal return;
- T_announce -> +7d abnormal return;
- ETH-relative 7d return;
- dose/response Spearman correlation between D and AR_7D;
- raw token return and BTC return separately.

No horizon or benchmark may replace the primary after inspection.

## Primary Development gates

Development SURVIVES only if ALL of the following pass:

G1. Source/data completeness:
12/12 frozen programs remain valid and have complete T0, D and market coverage before outcome analysis.

G2. Directional breadth:
At least 10 of 12 events have AR_7D > 0.
This corresponds to a one-sided exact sign-test p < 0.05 under p=0.5.

G3. Economic magnitude:
Median gross AR_7D > +0.80%.
This requires the median effect to exceed 2x the frozen 40 bp round-trip cost.

G4. Net viability:
Median NET_AR_7D > 0.

G5. Chain leave-one-out robustness:
Recompute median NET_AR_7D after removing all observations from each chain in turn.
At least 8 of the 9 leave-one-chain-out medians must remain > 0.

G6. Outlier concentration:
No single event may contribute >35% of the sum of absolute primary abnormal returns.

If any primary gate fails:
**NO_EDGE_DISCOVERY.**
No rescue subset, venue switch, horizon switch, sign switch, event replacement or threshold relaxation is permitted.

## Statistical reporting

Always report:
- N events and N chains;
- positive/negative counts;
- exact one-sided sign-test p-value;
- median and mean AR_7D;
- median NET_AR_7D;
- bootstrap 95% CI for median AR_7D using event-level resampling with fixed deterministic seed;
- each event's AR_7D and source identifiers;
- leave-one-chain-out medians;
- concentration share;
- dose/response rho as diagnostic only.

Bootstrap confidence interval is descriptive; it is not an additional rescue gate.

## Temporal boundaries

Development may use market history through 2025 only.
2026 outcomes are closed and must not be read.

## Governance boundaries

Research only.
No live trading.
No orders.
No leverage.
No wallets.
No account reads.
No authenticated/private exchange endpoints.
No exchange mutation.
No spending.
No merge to main.
No post-outcome tuning.

## Verdict vocabulary

- SOURCE_GATE_REVOKED / INSUFFICIENT_VALID_SAMPLE — if the frozen source/data prerequisite falls below 12 events before outcomes.
- BLOCKED_MARKET_COVERAGE — if the frozen 12-event market-capability requirement fails before outcome analysis.
- NO_EDGE_DISCOVERY — if Development opens and any primary gate fails.
- SURVIVES_DEVELOPMENT — only if every primary gate G1-G6 passes.

SURVIVES_DEVELOPMENT is not authorization for trading or promotion to production.
