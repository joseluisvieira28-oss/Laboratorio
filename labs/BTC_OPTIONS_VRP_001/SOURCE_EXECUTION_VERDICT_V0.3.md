# BTC-OPTIONS-VRP-001 — SOURCE / EXECUTION VERDICT V0.3

Date: 2026-09-27
Branch: `btc-options-vrp-source-verdict-v0.3`

## CANONICAL CURRENT STATE

**DISCOVERY_PASS_VRP_EXISTS / EXECUTION_NOT_ADJUDICATED / HISTORICAL_BBO_SOURCE_ACCESS_BLOCKED**

This is **not** `NO_EDGE`.
This is **not** `EDGE_SURVIVES`.
No executable-performance verdict exists yet for the frozen BBO execution MVE.

## DISCOVERY — PRESERVED POSITIVE PHENOMENON RESULT

Frozen MVE: `OVRP-DVOL-RV30-001`
Period: 2021-04-01 through 2024-11-28
Weekly observations: 192

Canonical Discovery run: `35067813949`

Observed:
- n = 192
- mean VRP = 1239.501861537634
- median VRP = 1133.9720368528974
- mean IV-RV vol gap = 10.429882697652479
- positive fraction = 0.7447916666666666
- HAC 95% CI = [674.1922655232069, 1804.8114575520613]
- block-bootstrap 95% CI = [696.3053046169578, 1793.3507436882755]
- yearly mean VRP:
  - 2021 = 2478.2137939815957
  - 2022 = 1531.0969236078256
  - 2023 = 601.4852142801566
  - 2024 = 582.5319684538925
- nonnegative years = 4/4

Classification remains:
**DISCOVERY_PASS_VRP_EXISTS**

## OLD EXECUTION MVE — CLOSED FOR SAMPLE, NOT PERFORMANCE

Frozen MVE: `OVRP-EXEC-ATM30-7D-STATICDELTA-001`
Canonical execution run: `35069743562`

The public direction-matched trade-print execution route produced:
- anchors = 192
- executable_n = 19
- minimum required executable_n = 120
- no eligible sell pair = 151
- no buyback fill pair = 22
- performance = null

Canonical classification:
**EXECUTION_DATA_LIQUIDITY_INSUFFICIENT**

The old MVE must not be reopened or rescued.

## NEW BBO EXECUTION MVE

Frozen MVE: `OVRP-EXEC-BBO-ATM30-7D-STATICDELTA-002`

The new MVE preserves the economic rules while requiring point-in-time executable BBO:
- same weekly Thursday 08:00 UTC anchors;
- 2021-04-01 through 2024-11-28;
- same-expiry same-strike call+put;
- 25–35 DTE, target 30 DTE;
- sell both option legs at executable bids;
- buy back at executable asks after seven days;
- BBO staleness <= 30 seconds;
- bid/ask sizes required;
- no midpoint substitution;
- initial static BTC-PERPETUAL delta hedge only;
- frozen fees and stress;
- minimum executable N = 120;
- 2025/2026 closed.

## HISTORICAL SOURCE ATTACK — CURRENT ADJUDICATION

### Tardis

Source-only V0.2 proved that historical Deribit `options_chain` + `quotes` can satisfy the frozen BBO schema on fixed 2021, 2022, 2023 and 2024 samples.

Classification:
**PAID_SOURCE_ROUTE_FEASIBLE**

Full historical access remains commercial and is not presently authorized/provided.

### Cryptarbitrage free 2024H1 parquet

Recovered and inspected:
- rows = 4,498,832
- positive BBO-price rows = 3,793,682
- in-band 25–35 DTE positive-BBO rows = 156,536
- distinct in-band UTC hours = 1,477
- distinct in-band UTC dates = 68
- paired call+put keys = 72,588
- bid-size field = absent
- ask-size field = absent

Frozen rich-geometry gate required >= 90 dates and executable-size evidence.

Classification:
**PRICE_ONLY_GEOMETRY_SPARSE_EXECUTION_SIZE_BLOCKED**

### optionsDX public sample / zero-price catalog

Public sample:
- 94,066 rows
- complete BBO price+size fields on all sample rows
- 458 unique instruments
- date = 2021-06-01
- complete BBO rows in frozen 25–35 DTE band = 0

Classification:
**OPTIONSDX_FREE_SAMPLE_SCHEMA_INSUFFICIENT**

Public catalog separately proved one active zero-price variation:
- 2021-06
- End of Day
- variation 1570
- USD 0

No zero-cost intraday full-history route has yet been proven. A full 200-combination public metadata census has been frozen separately, but no result from that queued census is used in this closeout.

### BRC

Published research proves a historical BTC-options order-book dataset existed for 2021-04-01 through 2022-04-01, but the current public BRC catalogue does not unambiguously expose that options subset to a new requester. Current access requires member/accreditation workflow.

Classification:
**BRC_OPTIONS_PUBLIC_ROUTE_NOT_ESTABLISHED**

### CoinAPI

A frozen source probe exists, but GitHub Actions readiness run `35456722984` returned:
**COINAPI_CREDENTIAL_ABSENT**

No key is available in the authorized runtime. No account/key acquisition is inferred or automated.

### Laevitas

The x402 historical options endpoint was successfully challenged and proved a paid route exists, but no payment was executed. The subsequent runner preflight passed, while the signer remained unavailable.

State:
**PAUSED_PENDING_USER_SIGNER — NOT FAILED**

### Volar / other commercial archives

Current public provider material shows a dense minute-level BTC options archive spanning 2021-06 through 2024-09, while full historical access and L2 bulk remain commercial. This is not a currently authorized zero-cost full-history BBO source.

### Official Deribit route

Current official historical endpoints expose historical instruments and trades, but no complete public historical BBO archive matching the frozen 192-anchor execution requirement has been established. Deribit itself points researchers needing comprehensive historical option quotes toward specialist data partners.

## FINAL CURRENT VERDICT

For `BTC-OPTIONS-VRP-001`:

- discovery phenomenon: **SUPPORTED**
- executable strategy edge: **NOT ADJUDICATED**
- old trade-print execution MVE: **CLOSED — INSUFFICIENT EXECUTABLE SAMPLE**
- new BBO execution MVE: **SOURCE ACCESS BLOCKED**
- public / anonymous historical route sufficient for >=120 frozen anchors: **NOT ESTABLISHED**
- paid / credential-gated route: **EXISTS**
- 2025: **LOCKED**
- 2026: **LOCKED**
- live trading: **NO**
- exchange mutation: **NO**
- promotion: **NO**
- micro-live: **NO**
- main merge: **NO**

Canonical classification:

> **DISCOVERY_PASS_VRP_EXISTS / EXECUTION_NOT_ADJUDICATED / HISTORICAL_BBO_SOURCE_ACCESS_BLOCKED**

## REOPEN CONDITIONS

The BBO execution MVE may be executed only if an authoritative pre-2025 point-in-time corpus becomes available that:
1. preserves exact Deribit BTC option identity and timestamps;
2. contains executable bid/ask prices and sizes;
3. supports the frozen entry/exit windows and <=30s staleness rule;
4. can produce at least 120 executable weekly anchors without changing any economic rule;
5. passes provenance and source integrity;
6. keeps 2025/2026 closed until separately authorized.

Qualifying unlock examples:
- authorized Tardis full-history access;
- an equivalently authoritative vendor corpus;
- a legitimately obtained research dataset that passes the exact BBO source gate;
- a future free route that independently proves the complete frozen requirements.

No threshold, date, strike, DTE, holding-period, hedge, fee, stress, sample or regime rescue is permitted.
