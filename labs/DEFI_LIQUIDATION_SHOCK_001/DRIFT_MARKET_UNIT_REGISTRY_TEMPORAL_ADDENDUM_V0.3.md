# DEFI-LIQUIDATION-SHOCK-001 — DRIFT MARKET UNIT REGISTRY TEMPORAL ADDENDUM V0.3

Date: 2026-09-26
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND

## Reason for addendum

Historical registry V0.2 correctly exposed one static-union conflict:

- spot marketIndex 0
- same mint: EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v (USDC)
- historical precisionExp observations: 9 and 6

Repository lineage shows:
- 2022-11-04T11:22:19Z commit 98142a595af924c604f393ef95e85fdb9c788c52 had the earlier configuration;
- 2022-11-04T17:07:15Z commit 11fe7b7666477346cc04d28d73713932b9d74591 is explicitly titled "sdk: fix quote precision to 1e6";
- first frozen successful Drift liquidation is later, at 2022-11-06T23:54:51Z.

Therefore a timeless union rule is too strict for a historically versioned registry.
The correction must not be collapsed or deleted; instead unit metadata is resolved against event time.

This addendum changes only source-registry semantics. It does not alter the frozen event population,
instruction classes, timestamps, or any economic rule.

## Temporal registry rule

For each spot marketIndex:
1. scan every authenticated historical MainnetSpotMarkets snapshot in chronological commit order;
2. extract source-authoritative (mint, decimals);
3. emit a new temporal version only when (mint, decimals) changes;
4. each version is effective from its source commit timestamp until the next version timestamp;
5. preserve all historical versions, including corrected/superseded versions.

For every frozen realized event with spot market index i at timestamp T:
- select the latest temporal registry version for i with effective_from <= T;
- require exactly one such version;
- require mint and decimals non-null.

No version may be selected using price, return, PnL or future economic outcomes.

## Same-timestamp/source ordering

If two source commits for the same marketIndex have the same commit timestamp and conflicting unit pairs:
FAIL_CLOSED unless repository parent ordering gives a unique later descendant.

## Perp registry

Perp unit semantics remain protocol-native:
- base precision 1e9 / exponent 9
- quote precision 1e6 / exponent 6

Historical market identity is also resolved by latest source snapshot at or before event timestamp.

## Population PASS

After DRIFT_FIELD_ENRICHMENT_POPULATION_PASS, every observed event market index must resolve temporally.

PASS:
DRIFT_MARKET_UNIT_REGISTRY_POPULATION_PASS

No version at/before event:
DRIFT_MARKET_UNIT_REGISTRY_PENDING_SOURCE_COMPLETION

Conflicting or ambiguous temporal version:
DRIFT_MARKET_UNIT_REGISTRY_BLOCKED_FAIL_CLOSED

## Firewall

prices=false
oracle_values=false
usd_notional=false
returns=false
pnl=false
direction=false
economic_outcomes=false
token_amounts=false
requested_max_amount_values=false
limit_price_values=false
protected_2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
account_creation=false
post_outcome_tuning=false
merge_main=false
