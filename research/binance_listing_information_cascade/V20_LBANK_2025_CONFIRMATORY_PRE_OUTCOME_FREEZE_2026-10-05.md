# BINANCE-LISTING-INFORMATION-CASCADE-001 — V2.0 LBANK 2025 CONFIRMATORY PRE-OUTCOME FREEZE
Date: 2026-10-05
Status: FROZEN BEFORE ANY 2025 MARKET-OUTCOME INSPECTION

## Purpose and lineage
V0.4 and V1.0 are permanently closed as SOURCE_BLOCKED and MUST NOT be amended.

V2.0 is a separate outcome-independent confirmatory protocol.
Prior source-only feasibility and identity evidence may be reused because no 2025 return, price-outcome, PnL, MFE, MAE, delayed-return or cost-adjusted outcome has ever been opened.

2024 remains quarantined.
2026 remains unopened.

## Claim under test
Does the Binance public spot-listing announcement information shock that survived clean 2022-2023 discovery remain a positive delayed-entry effect in 2025 after a frozen conservative transaction-cost stress?

## Fixed 2025 sample
The sample is fixed to the same 12 outcome-unopened observations established by prior source-only work:
1. AIXBT
2. CGPT
3. COOKIE
4. SYRUP
5. KMNO
6. PUMP
7. AVNT
8. ASTER
9. GIGGLE
10. F (SynFutures)
11. BANK (Lorenzo Protocol)
12. MET (Meteora)

No observation may be added, removed, replaced or filtered after this freeze.

## Official T0 values
T0 is the official Binance public CMS releaseDate already established in the outcome-blind 2025 census.

Frozen T0 milliseconds:
- AIXBT: 1736499327639
- CGPT: 1736499327639
- COOKIE: 1736499327639
- SYRUP: 1746530720814
- KMNO: 1746530720814
- PUMP: 1757590673797
- AVNT: 1757908021934
- ASTER: 1759736929954
- GIGGLE: 1761361338417
- F: 1761361338417
- BANK: 1763028026501
- MET: 1763028026501

## Exact frozen venue bindings
Bindings are fixed BEFORE any V2.0 outcome inspection:
- AIXBT -> KUCOIN spot
- CGPT -> KUCOIN spot
- COOKIE -> KUCOIN spot
- SYRUP -> LBANK spot
- KMNO -> KUCOIN spot
- PUMP -> KUCOIN spot
- AVNT -> KUCOIN spot
- ASTER -> KUCOIN spot
- GIGGLE -> KUCOIN spot
- F -> KUCOIN spot
- BANK -> BITGET spot
- MET -> KUCOIN spot

No runtime venue shopping.
No fallback after this freeze.

## SYRUP / LBANK pre-outcome identity and timing evidence
Official LBank listing evidence identifies the spot market as SYRUP/USDT for Syrup.fi / Maple and states spot trading opened 2025-03-13 03:30 UTC, well before Binance T0 2025-05-06.

Official LBank API documentation states that public GET /v2/kline.do supports:
- symbol
- size up to 2000
- type=minute1
- a required timestamp in seconds

This evidence contains no 2025 return outcome.

## Mandatory source usability
Each fixed venue binding must provide public unauthenticated 1m data sufficient for:
1. at least one bar timestamp <= T0-24h;
2. a valid pre-T0 bar in [T0-10m, floor(T0 minute));
3. all first five complete post-T0 event minutes;
4. a non-empty T0-24h..T0-1h baseline;
5. strictly positive median non-overlapping 5m baseline volume.

Prior outcome-blind source evidence already established these conditions for the 11 non-SYRUP bindings.

Before V2.0 outcomes may open, SYRUP/LBANK must pass a source-only probe emitting only counts/booleans.

If SYRUP/LBANK fails mandatory source usability:
V2.0 verdict = SOURCE_BLOCKED.
No alternate venue may be substituted within V2.0.

## Information layer
P0 = close of final complete 1m bar strictly before floor(T0 to minute).

Report R1/R5/R15/R60, MFE/MAE, and first-5m volume shock using the same frozen information-layer semantics as V0.4/V0.3.
This layer is secondary and cannot override the primary execution verdict.

Information replication gate, ALL required:
- n >= 12
- median R15 > +0.75%
- R15 hit-rate >=65%
- median R5 > +0.50%
- median 5m volume shock >=2x
- leave-one-out median R15 >0
- no single observation >35% of summed positive R15

## PRIMARY execution layer
No entry at T0.

Entry time:
first full minute boundary at least 60 seconds after T0.

Implementation:
entry_time = ceil_to_minute(T0 + 60 seconds)

Entry price:
OPEN of the exact 1m bar whose open timestamp equals entry_time.

Primary 15-minute exit:
CLOSE of the 15th full 1m bar beginning at entry_time.
Therefore the target bar open timestamp is:
entry_time + 14 minutes.

Secondary delayed horizons:
5 full minutes -> target bar open = entry_time + 4 minutes
60 full minutes -> target bar open = entry_time + 59 minutes

## BTC-relative execution return
For each venue, BTC/USDT is measured on the SAME venue and same exact entry/target bar timestamps.
gross_R15_exBTC = asset_gross_R15 - BTC_gross_R15.

## Frozen transaction-cost stress
Primary:
- 50 bps all-in round trip
- 25 bps adverse entry
- 25 bps adverse exit

net50 = [exit*(1-0.0025)] / [entry*(1+0.0025)] - 1

Secondary sensitivity only:
- net25: 12.5 bps adverse each side
- net100: 50 bps adverse each side

No cost level may be changed after outcomes.

## PRIMARY EXECUTION SURVIVAL GATE — ALL required
- n >= 12
- median delayed net50 R15 > 0
- delayed net50 R15 positive hit-rate >=60%
- leave-one-out median delayed net50 R15 >0
- no single observation contributes >35% of summed positive delayed net50 R15
- median delayed gross R15 exBTC >0

Verdicts:
- source failure before outcomes -> SOURCE_BLOCKED
- n >= 12 and any primary execution gate fails -> NO_EXECUTABLE_EDGE_HOLDOUT
- all primary execution gates pass -> SURVIVES_EXECUTION_HOLDOUT

## Anti-hindsight
After this freeze:
- no event changes
- no T0 changes
- no venue changes
- no direction changes
- no horizon changes
- no cost changes
- no threshold changes
- no outlier removal
- no post-outcome tuning

Purely technical fixes may preserve frozen semantics but may not alter scientific meaning.

## Governance
Research-only.
No merge to main.
No live trading.
No orders.
No authenticated/private exchange endpoints.
No account reads.
No wallets.
No 2026 outcomes.
