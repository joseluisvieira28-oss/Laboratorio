# BINANCE-LISTING-INFORMATION-CASCADE-001 — V1.0 INDEPENDENT 2025 CONFIRMATORY PRE-OUTCOME FREEZE
Date: 2026-10-05
Status: FROZEN BEFORE ANY 2025 MARKET-OUTCOME INSPECTION

## Purpose
V0.4 is permanently closed as SOURCE_BLOCKED and MUST NOT be amended or reinterpreted.

V1.0 is a separate outcome-independent confirmatory protocol. It is allowed to use prior SOURCE-ONLY feasibility and identity evidence because no 2025 return, price-outcome, PnL, MFE, MAE, delayed-return or cost-adjusted outcome has ever been opened.

2024 remains quarantined.
2026 remains unopened.

## Claim under test
Does the Binance public spot-listing announcement information shock that survived clean 2022-2023 discovery remain a positive delayed-entry effect in 2025 after a frozen conservative transaction-cost stress?

## Event authority and fixed 2025 sample
T0 authority remains the official Binance public CMS releaseDate.

The fixed V1.0 sample is the 12 observations already established by outcome-blind V0.4 source/identity work:
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

No event may be added, removed, replaced or filtered after this freeze.

## Exact frozen venue bindings
These bindings are fixed BEFORE any V1.0 outcome inspection:

- AIXBT -> KUCOIN spot
- CGPT -> KUCOIN spot
- COOKIE -> KUCOIN spot
- SYRUP -> MEXC spot
- KMNO -> KUCOIN spot
- PUMP -> KUCOIN spot
- AVNT -> KUCOIN spot
- ASTER -> KUCOIN spot
- GIGGLE -> KUCOIN spot
- F -> KUCOIN spot
- BANK -> BITGET spot
- MET -> KUCOIN spot

There is no runtime venue shopping and no fallback after this freeze.

## SYRUP / MEXC pre-outcome identity evidence
Official MEXC listing evidence identifies the market as Maple Finance (SYRUP) / USDT and states trading opened 2024-11-25 09:00 UTC, well before the Binance T0 used by this protocol.

This identity/source evidence contains no 2025 outcome return.

## Mandatory source usability
Every fixed venue binding must provide public unauthenticated 1m data sufficient for:
1. at least one bar timestamp <= T0-24h;
2. a valid pre-T0 bar in [T0-10m, floor(T0 minute));
3. all first five complete post-T0 event minutes;
4. a non-empty T0-24h..T0-1h baseline;
5. strictly positive median non-overlapping 5m baseline volume.

Prior outcome-blind source evidence already established these conditions for the 11 non-SYRUP bindings.

Before V1.0 outcomes may open, SYRUP/MEXC must pass a new source-only probe emitting only counts/booleans.

If SYRUP/MEXC fails mandatory source usability:
V1.0 verdict = SOURCE_BLOCKED.
No alternate venue may be substituted.

## Information layer
P0 = close of final complete 1m bar strictly before floor(T0 to minute).

Report:
- R1
- R5
- R15
- R60
- MFE/MAE
- first-5m volume shock

Information replication gate, ALL required:
- n >= 12
- median R15 > +0.75%
- R15 hit-rate >= 65%
- median R5 > +0.50%
- median volume shock >= 2x
- leave-one-out median R15 > 0
- no single observation >35% of summed positive R15

This layer is descriptive/secondary for V1.0 and cannot override execution failure.

## PRIMARY execution layer
No entry at T0.

Entry time = first full minute boundary at least 60 seconds after T0.
Entry price = OPEN of that 1m bar.
Primary horizon = 15 full minutes.
Exit price = CLOSE of the 15th full 1m bar beginning at entry_time.

Also report delayed 5m and 60m returns as secondary diagnostics.

## Frozen transaction-cost stress
Primary:
- 50 bps all-in round trip
- modeled as 25 bps adverse entry and 25 bps adverse exit
- net50 = [exit*(1-0.0025)] / [entry*(1+0.0025)] - 1

Secondary sensitivities only:
- net25
- net100

No cost level may be changed after outcomes.

## PRIMARY EXECUTION SURVIVAL GATE — ALL required
- n >= 12
- median delayed net50 R15 > 0
- delayed net50 R15 positive hit-rate >= 60%
- leave-one-out median delayed net50 R15 > 0
- no single observation >35% of summed positive delayed net50 R15
- median delayed gross R15 ex-BTC > 0

Verdicts:
- source failure before outcomes -> SOURCE_BLOCKED
- n >= 12 and any primary execution gate fails -> NO_EXECUTABLE_EDGE_HOLDOUT
- all primary execution gates pass -> SURVIVES_EXECUTION_HOLDOUT

## Anti-hindsight
After this freeze:
- no event changes;
- no T0 changes;
- no venue changes;
- no direction changes;
- no horizon changes;
- no threshold changes;
- no cost changes;
- no outlier removal;
- no post-outcome tuning.

Purely technical fixes may preserve frozen semantics but may not change scientific meaning.

## Governance
Research-only.
No merge to main.
No live trading.
No orders.
No authenticated/private exchange endpoints.
No account reads.
No wallets.
No 2026 outcomes.
