# CED-1D AVAX20 — V3 BOOKDEPTH CAPACITY CORROBORATION FREEZE — 2026-09-18

**Status:** FROZEN BEFORE AVAXUSDT 2025 BOOKDEPTH ACCESS  
**Branch:** `ced-1d-v3-byte-recovery-2026-09-17`  
**Candidate:** `CED1D-0031` only.

## Why this gate exists

The first frozen aggTrades execution proxy remains immutable and remains FAIL on its own predeclared 99% fill-visibility requirement:

- run: `35342472136`
- artifact: `10546145535`
- digest: `sha256:5b784d64aa9d2741f9c16c331d7e75f9d428bf5912e5fe8e59815292df288d84`
- observed-print leg coverage: 674/714 = 94.3978%
- observed-print complete-pair coverage: 320/357 = 89.6359%

All economic/latency/cost/concentration gates on the 320 observable pairs passed:
- BASE executable funded mean: +24.1642 bps
- BASE PF: 1.1339
- STRESS executable funded mean: +22.1642 bps
- mean total nonfunding proxy: 7.0435 bps
- p95 total nonfunding proxy: 8.7297 bps
- median observed leg latency: 516 ms
- p95 observed leg latency: 3406.65 ms
- concentration: PASS

Absence of a same-side aggressive print is not proof that passive opposite-side order-book liquidity was absent. Therefore the first FAIL is treated as a **print-observability fill-proxy failure**, not automatically as proof of impossible market execution. This second gate does not alter, rerun, widen or rescue the first proxy.

## Immutable population

Evaluate **all 714 entry/exit legs** belonging to the exact 357 inference-eligible CED1D-0031 2025 events.

No selection of only prior misses is allowed.

Execution target remains exactly **100 USDT per leg**.

## Source

Official Binance Public Data, USD-M Futures daily `bookDepth`:

`https://data.binance.vision/data/futures/um/daily/bookDepth/AVAXUSDT/AVAXUSDT-bookDepth-YYYY-MM-DD.zip`

Every accessed daily archive must pass:
- provider `.CHECKSUM`;
- local SHA256 equality;
- ZIP CRC;
- schema `timestamp,percentage,depth,notional`;
- date bounds;
- finite nonnegative depth/notional;
- unique percentage row per snapshot.

Only 2025 dates required by the immutable 714 legs may be accessed.

No 2026 source may be opened.

## Dataset semantics

The source is treated only as a **capacity/depth corroboration surface**, not as historical BBO.

Frozen signed-band mapping:
- negative percentage = bid-side cumulative depth;
- positive percentage = ask-side cumulative depth;
- BUY leg consumes ask-side capacity -> use `percentage = +1`;
- SELL leg consumes bid-side capacity -> use `percentage = -1`.

Only the ±1% cumulative band is used.

This gate does **not** infer exact spread, exact best bid/ask, exact fill price or sub-1% book shape from bookDepth.

## Temporal matching

For each immutable leg reference timestamp:
1. use the latest bookDepth snapshot with timestamp <= leg reference timestamp;
2. snapshot age must be <= **60 seconds**;
3. no future snapshot may be used;
4. no interpolation or nearest-future substitution is allowed.

The 60-second maximum is frozen before AVAXUSDT bookDepth access and reflects the publicly observed approximately-30-second sampling cadence with one full additional cadence of tolerance.

## Capacity metric

For the required side at ±1%, use the source `notional` field as cumulative quote-side capacity.

A leg is `CAPACITY_OBSERVED` when:
- a valid prior snapshot exists within 60s;
- the required ±1% side row exists;
- cumulative notional >= **100 USDT**.

No scaling down of 100 USDT is allowed.

Report:
- snapshot coverage rate;
- capacity-observed rate;
- minimum, p05, median and p95 cumulative notional at the required side;
- snapshot-age median/p95/max;
- month-by-month coverage;
- prior aggTrades-miss subset capacity only as a diagnostic, never as the primary denominator.

## Capacity corroboration PASS

PASS requires all:
- >=99% of all 714 legs have a valid prior snapshot <=60s;
- >=99% of all 714 legs have required-side cumulative ±1% notional >=100 USDT;
- every calendar month containing candidate legs has >=95% capacity-observed coverage;
- no 2026 access;
- no malformed/failed checksum source silently omitted.

A missing daily archive, bad checksum, stale snapshot or missing side counts as a failed leg for the primary denominator.

## Composite V3 execution adjudication — prospectively frozen here

The immutable first aggTrades proxy is not rewritten. After this capacity gate:

**COMPOSITE_EXECUTION_FEASIBLE** only if:
1. bookDepth capacity corroboration PASS;
2. first aggTrades economics retain:
   - >=300 complete pairs;
   - BASE funded mean >0;
   - BASE PF >1;
   - STRESS funded mean >=0;
   - mean nonfunding proxy <=14 bps;
   - p95 nonfunding proxy <=20 bps;
   - median observed latency <=1000ms;
   - p95 observed latency <=5000ms;
   - concentration PASS;
3. 2025 reference OOS remains independently positive with N=357 and PF>1;
4. fee assumption remains no lower than the already frozen taker-only 4 bps/fill BASE, 5 bps/fill STRESS.

The first print-fill-rate FAIL remains explicitly disclosed as a fragility. It is not deleted or relabelled PASS.

If the bookDepth gate fails, execution remains unresolved/failed and no Tier 2 promotion occurs.

If the composite gate passes, the execution-feasibility hard requirement of Promotion Policy V3 may be considered satisfied **only for tiny 100-USDT research notional**. This still does not authorize live trading or production.

## Prohibitions

No 2026+. No event deletion. No signal/direction/lookback/horizon change. No maker assumption. No fee reduction. No widening of the first aggTrades 5-second rule. No live trading. No orders. No wallets. No exchange mutation. No alerts/webhooks. No merge main.
