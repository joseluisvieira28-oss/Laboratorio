# BTC-DVOL-FUTURES-TERMSTRUCTURE-001 — LIFECYCLE SOURCE CLOSEOUT V0.1

Date: 2026-09-16

## Canonical lifecycle gate

- Source gate: `DVOL-TS-LIFECYCLE-SOURCE-001`
- Canonical GitHub Actions run: `35087694157`
- Job: `104766314303`
- Head SHA: `895f414de9befec1c124d2ac75e09e3ac0c5f1c9`
- Artifact: `btc-dvol-futures-lifecycle-source-35087694157-1`
- Artifact ID: `10442044415`
- Artifact ZIP SHA-256: `2d150aec6a29b4b8940d3e2e1da7299ca62bba1baa05ca288f25606232ed400b`
- Result SHA-256: `59f326aa21a4565c2f68b6e382ee5ddde8371bec406f5b7bc86000428a6cf9f4`

## Classification

`LIFECYCLE_SOURCE_DATA_INSUFFICIENT`

This is **NOT `NO_EDGE`**. No DVOL price level, futures price distribution, direction statistic, basis, convergence return, strategy return, PnL, or protected 2025/2026 outcome was opened.

## What the source-density attack actually found

The deterministic calendar enumeration tested 92 Wednesday candidate names from 2023-03-29 through 2024-12-25. It recovered 18 accepted BTC DVOL futures contracts. All 18 accepted contracts independently met the frozen qualifying-source definition of at least 20 ordinary public trades and at least 5 unique active UTC trading days.

Across those 18 accepted contracts:

- ordinary public historical trades: **11,194**
- aggregate active contract-days: **576**
- qualifying contracts: **18 / 18**
- qualifying expiration-quarter coverage: **7 quarters** (`2023-Q2` through `2024-Q4`)
- core trade-field coverage: **100%**
- auxiliary `index_price` / `mark_price` field coverage: **100%**
- confirmed accepted contracts: **18** versus frozen minimum **12**
- qualifying contracts: **18** versus frozen minimum **8**
- aggregate active contract-days: **576** versus frozen minimum **80**
- qualifying calendar quarters: **7** versus frozen minimum **6**

Observed accepted contract counts were not used to open or tune any economic test.

## The single frozen gate that failed

The exact metadata-integrity rate was **18/19 = 0.9473684210526315**, below the prospectively frozen requirement of **1.0**.

The sole exact-name metadata rejection was `BTCDVOL_USDC-26APR23`. Its archived metadata identifies it as a BTC DVOL future with `price_index=btcdvol_usdc`, but its `creation_timestamp=1679566050000` (2023-03-23T10:07:30Z) predates the authority's frozen lower acceptance bound of 2023-03-27T00:00:00Z. Its expiration timestamp is 2023-04-26T08:00:00Z.

Because every gate was conjunctive, this one metadata-integrity failure forces the canonical classification `LIFECYCLE_SOURCE_DATA_INSUFFICIENT` despite the large observed trade-tape density. The lower-bound acceptance rule may not be waived after seeing this result under the same gate ID.

## Governance

The exact lifecycle source gate is closed as specified. No threshold, candidate date, acceptance bound, qualifying-contract definition or source window may be changed to turn this result into a PASS under `DVOL-TS-LIFECYCLE-SOURCE-001`.

The earlier run `35087414533` was a pre-outcome technical failure on provider-specific exact-name miss semantics. That transport issue was documented prospectively and repaired without changing the scientific contract before canonical run `35087694157`.

`access_2025=false`. `access_2026=false`. No live trading, exchange mutation or merge to main occurred.

## Scientific interpretation

There is strong **source-engineering evidence** that pre-2025 BTC DVOL futures historical trade tape is not generally sparse: 18 accepted contracts produced 11,194 ordinary public trades over 576 active contract-days and seven expiration quarters. However, this exact prospective source gate did not satisfy every frozen integrity condition, so **Discovery is not authorized from this gate**.

Any future DVOL-futures study must use a new source-gate ID and a prospectively justified population/source definition. It may not use economic outcomes from this gate because none were opened.
