# POB-STRIKE-BINANCE-CFRTI-001 — PRE-SOURCE CHILD AUTHORITY V0.1

Date: 2026-09-27
Parent: PREDICTION-ORACLE-BASIS-001
Status: FROZEN_PRE_SOURCE / OUTCOME_BLIND / RESEARCH_ONLY
Branch: prediction-oracle-basis-v0.1

## Why this child exists

The prior child POB-15M-CHAINLINK-CFRTI-001 is terminally SOURCE_RULE_PROVENANCE_BLOCKED because first-party Kalshi materials did not prove how the rolling KXBTC15M Target Price is initialized.

This child does not reopen or relabel that blocker.

It tests a materially distinct contract geometry in which the threshold/strike is explicit on both venues and therefore does not depend on reconstructing a hidden or under-specified target initialization rule.

## Frozen source geometry

Polymarket candidate family:
- BTC threshold markets of the form "Bitcoin above ___ on <date>?"
- nominal strike is explicit in the market question;
- resolution time is fixed by the market rules;
- resolution source is Binance BTC/USDT;
- applicable source object is the specified Binance candle close.

Kalshi candidate family:
- KXBTCD directional BTC threshold markets;
- nominal displayed threshold is explicit;
- close/expiration time is explicit;
- terminal settlement source is CF Benchmarks BRTI using the documented final-minute averaging method;
- the encoded Kalshi threshold may be one cent below the displayed integer threshold (for example T85999.99 for "$86,000 or above").

## Primary source question

Does a reproducible current population exist in which a Polymarket threshold contract and a Kalshi KXBTCD threshold contract have:
- the same BTC underlying;
- the same wall-clock resolution instant;
- the same nominal displayed strike;
- the same binary direction;
- a known and mechanically enumerable tie-boundary difference;
- distinct reference-price constructions;
- machine-readable public executable quote/depth routes on both venues?

This is a SOURCE/DATA question only. It is not a claim of arbitrage or edge.

## Contract classification — frozen

Every candidate pair must be assigned exactly one source classification before any economic analysis:

1. MATCHED_STRIKE_TIME_REFERENCE_DIFF_TIE_1C
   - same nominal strike;
   - same resolution instant;
   - Polymarket condition is strictly greater than nominal strike;
   - Kalshi condition is at/above the nominal cent boundary encoded as > nominal-0.01 or equivalent official rule text;
   - settlement references differ as documented.

2. NON_EQUIVALENT_TIME
3. NON_EQUIVALENT_STRIKE
4. NON_EQUIVALENT_DIRECTION
5. NON_EQUIVALENT_SETTLEMENT_WINDOW
6. NON_EQUIVALENT_OTHER
7. SOURCE_RULE_PROVENANCE_BLOCKED

The primary source gate may advance on class (1). It must never call class (1) "EXACT_EXCEPT_ORACLE"; the 1-cent boundary is explicit and must remain visible in all later science.

## Economic mechanism — pre-outcome statement

If the two markets price their economically near-identical explicit-strike payoff as fungible while their terminal reference-price constructions differ, a contract-basis wedge can exist near the strike.

Potential wedge sources:
- Binance BTC/USDT single-candle close versus CF Benchmarks BRTI final-minute average;
- BTC/USDT versus multi-venue USD reference composition;
- the explicit 1-cent tie boundary;
- fragmented venue collateral/access;
- different fee/spread/depth states;
- asynchronous quote updates.

Potential payer:
participants who ignore settlement-reference and contract-boundary basis when comparing the two binary claims.

## Failure mode

The mine fails or is blocked if:
- no same-time same-nominal-strike population exists;
- rules reveal a larger semantic mismatch than reference/tie construction;
- public executable order-book routes cannot be captured reproducibly;
- quote timestamps cannot be synchronized prospectively;
- plausible contract-basis magnitude is structurally smaller than friction/capacity requirements;
- market/rule schemas change such that deterministic matching breaks.

## Source gate allowed outputs

Allowed:
- public metadata and rule text;
- immutable identifiers;
- nominal strikes and encoded thresholds;
- open/close timestamps;
- rule hashes;
- public order-book bid/ask/size fields;
- source timestamps;
- source coverage/missingness;
- matched-pair counts;
- source-only classification;
- raw hashes and receipts.

Forbidden:
- PnL;
- expected return;
- win rate;
- "arbitrage profit";
- threshold optimization;
- best hour/date/strike;
- selecting pairs by observed profitability;
- backfilled trade simulation;
- orders;
- authenticated trading endpoints;
- capital;
- exchange mutation;
- main merge.

## Source/Data Gate PASS requirements

Before any economic test:
1. >=1 class-(1) current matched pair proven from source fields/rules;
2. public acquisition route for both venues;
3. Polymarket YES/NO CLOB token identity and executable book route proven;
4. Kalshi executable bid/ask+size route proven;
5. no future-nearest join;
6. no silent imputation;
7. UTC timestamp integrity established;
8. rule text/source identity hashed;
9. exact nominal-strike and encoded-boundary mapping preserved;
10. source manifest and SHA256 receipt preserved.

A one-time source-shape PASS does not authorize economics. A later prospective synchronized-capture protocol must be frozen separately.

## Outcome firewall

This child may inspect only source geometry and current public quote/depth plumbing needed to prove executability.

No matured contract outcome, strategy result, PnL, hit rate, conditional profitability or optimized selection may be computed in this phase.

## Governance

Research-only.
Fail closed.
No live trading.
No exchange mutation.
No main merge.
No rescue of the blocked 15m child.
No post-outcome tuning.
