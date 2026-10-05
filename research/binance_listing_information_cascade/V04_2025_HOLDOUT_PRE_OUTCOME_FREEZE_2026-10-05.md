# BINANCE-LISTING-INFORMATION-CASCADE-001 — V0.4 2025 HOLDOUT PRE-OUTCOME FREEZE
Date: 2026-10-05
Status: FROZEN BEFORE ANY 2025 MARKET-OUTCOME INSPECTION
Parent discovery: V0.3 authoritative SURVIVES_INFORMATION_DISCOVERY
Parent discovery closeout: 4c6d1df4da14ba9ff5b82f6e506e12f1e5147e7d

## Claim under test
Does the Binance public spot-listing announcement information shock discovered in clean 2022-2023 data remain a positive delayed-entry effect in an independent 2025 holdout after a conservative transaction-cost stress?

2024 is quarantined and MUST NOT be used.
2026 remains unopened and MUST NOT be used.

## Holdout period
Calendar year 2025 only.

## Event authority
Official Binance public CMS catalog.
T0 = exact official CMS releaseDate for announcements whose title begins with "Binance Will List ".

Mechanical exclusions, determined without price outcomes:
- stablecoins / fiat-like tokens;
- wrapped/staked representations where identity is not the announced underlying;
- ticker collisions without defensible identity mapping;
- TGE / genesis cases without >=24h continuous pre-T0 trading on an eligible comparison venue.

Multi-asset announcements are separate observations sharing T0.

## Frozen source hierarchy and source usability
Venue hierarchy: KuCoin spot first, Bitget spot second.
No venue shopping based on returns.

A venue is source-usable only if public unauthenticated 1m data provide:
1. at least one bar timestamp <= T0-24h;
2. a valid pre-T0 bar in [T0-10m,T0);
3. the first five complete post-T0 event minutes;
4. a non-empty T0-24h..T0-1h baseline with strictly positive median non-overlapping 5m volume.

If KuCoin is not source-usable for mandatory metrics, Bitget may be used only if it independently passes these source-only conditions.

## Information layer — unchanged descriptive replication
P0 = close of final complete 1m bar strictly before floor(T0 to minute).
Report R1/R5/R15/R60, MFE/MAE, and 5m volume shock exactly as in V0.3.
Information replication gate remains the V0.3 gate and is reported independently:
- n >= 12
- median R15 > +0.75%
- R15 hit-rate >=65%
- median R5 > +0.50%
- median volume shock >=2x
- leave-one-out median R15 >0
- no single observation >35% of summed positive R15.

## Execution layer — PRIMARY V0.4 holdout claim
No entry at T0.
Entry time = first full minute boundary at least 60 seconds after T0.
Entry price = OPEN of that 1m bar.
Primary horizon = 15 full minutes, preserving the original R15 scientific horizon rather than choosing the best V0.3 delayed horizon.
Exit price = CLOSE of the 15th full 1m bar beginning at entry_time.

Also report 5m and 60m delayed returns, but they are secondary.

## Frozen modeled cost stress
This is a model stress, NOT a claim about exact historical fee tiers.
Primary cost envelope = 50 bps all-in round trip, modeled symmetrically as 25 bps adverse entry and 25 bps adverse exit:
net50 = [exit*(1-0.0025)] / [entry*(1+0.0025)] - 1.

Secondary sensitivity:
- net25: 12.5 bps adverse each side;
- net100: 50 bps adverse each side.

No cost level may be changed after outcomes.

## PRIMARY EXECUTION SURVIVAL GATE — ALL required
- n >= 12 valid holdout observations;
- median delayed net50 R15 > 0;
- delayed net50 R15 positive hit-rate >=60%;
- leave-one-out median delayed net50 R15 remains >0;
- no single observation contributes >35% of summed positive delayed net50 R15;
- median delayed gross R15 ex-BTC >0.

If n<12 because the frozen public sources are insufficient: SOURCE_BLOCKED.
If n>=12 but any primary execution gate fails: NO_EXECUTABLE_EDGE_HOLDOUT.
If all primary execution gates pass: SURVIVES_EXECUTION_HOLDOUT.

Information-layer replication does not override an execution-layer failure.

## Anti-hindsight
After this freeze:
- no event filtering based on returns;
- no T0 changes;
- no venue changes based on performance;
- no horizon changes;
- no direction changes;
- no threshold/cost changes;
- no outlier removal;
- no post-outcome tuning.

Technical fixes may preserve the frozen meaning but may not alter it.

## Governance
Research-only.
No merge to main.
No live trading.
No orders.
No authenticated/private exchange endpoints.
No account reads.
No wallets.
No 2026 outcomes.
