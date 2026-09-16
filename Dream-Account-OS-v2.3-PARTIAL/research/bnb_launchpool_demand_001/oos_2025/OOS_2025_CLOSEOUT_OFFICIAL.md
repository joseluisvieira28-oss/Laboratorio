# BNB-LAUNCHPOOL-DEMAND-001 — 2025 V2 OOS CLOSEOUT

Protocol: `BNB-LAUNCHPOOL-DEMAND-001-V2-OOS-2025-V0.1`  
Parent MVE: `BLP-BNBBTC-24H-001`  
Date: `2026-09-16`  
Branch: `bnb-launchpool-demand-v2-oos-2025-v01`  
Governing policy: `ND-PROMOTION-POLICY-V2.0-FROZEN-2026-09-14`  
Support path tested: `PATH_2_GENUINELY_INDEPENDENT_OOS_REPLICATION`

## Immutable historical state

The parent Discovery verdict remains **DISCOVERY_FAIL_NO_PROMOTION**. This OOS closeout does not rewrite the parent result.

Pre-OOS V2 classification: **TIER 3 — WATCHLIST / NEAR-DIAMOND CANDIDATE**.

## Prospective freeze and provenance

The 2025 OOS protocol was frozen before any calendar-2025 source or market outcome was opened.

Official Binance Launchpool source gate found and validated project numbers 64 through 71, all in calendar 2025 and all with explicit BNB locking/staking. Source gate classification: `SOURCE_DATA_PASS`.

Canonical 2025 event manifest SHA256: `437a5f1d3ec591d801ccc951911252888374544394f4f5def35f9660534979b4`.

Binance Data Vision BNBBTC 15m market-source audit validated all 12 calendar-2025 monthly archives against official checksums, with zero duplicate timestamps and zero selected execution-path failures. Market-source classification: `MARKET_SOURCE_DATA_PASS`.

Market archive manifest SHA256: `699215ba13055b12dae4b01be09c9535066d5ef3bc7bcd314b1787358915dacf`.

Market-source artifact ID: `10464554979`.  
Artifact ZIP SHA256: `f777558a3643c3411868ab7b49bce2fcb1c728a2a8d317b8d47deb4e8c575fcd`.

2026 market outcomes were not opened.

## Frozen execution rule

Unchanged from the parent MVE:

- LONG `BNBBTC`.
- Signal at canonical Binance Launchpool publication time.
- Adjacent announcements <=60 minutes form one information cluster.
- Entry at first 15m BNBBTC open strictly after signal.
- Exit exactly 24 hours later at 15m open.
- One active trade at a time; overlapping later signals suppressed.
- No stop, no target, no leverage.
- BASE round-trip cost: 20 bps.
- STRESS round-trip cost: 30 bps.
- Only the 16 frozen entry/exit open values were parsed; high/low/close/volume remained unopened.

## 2025 independent OOS result

Resolved trades: **8**.

- Gross mean: **+77.6174 bps/trade**
- BASE NET20 mean: **+57.6174 bps/trade**
- BASE median: **+38.2528 bps/trade**
- BASE PF: **2.5478**
- BASE win rate: **62.5%**
- BASE total: **+460.9391 bps**
- STRESS NET30 mean: **+47.6174 bps/trade**
- STRESS PF: **2.1621**
- STRESS total: **+380.9391 bps**
- Compounded BASE return across the eight non-overlapping trades: **+4.5809%**
- Compounded BASE max drawdown: **2.6114%**
- Bootstrap 95% CI for BASE mean: **[-54.1406, +186.5255] bps/trade** — report-only under the frozen V2 Path 2 protocol.

## V2 Path 2 gates

PASS:

- source provenance clean and reproducible;
- no leakage/hindsight/post-outcome selection;
- minimum resolved sample (8/8);
- BASE mean > 0;
- BASE PF >= 1;
- expected LONG BNBBTC sign correct;
- zero unresolved selected execution paths;
- zero source-rule deviations;
- zero trading-rule deviations;
- no fatal V2 execution/risk pathology.

FAIL:

- maximum single-trade share of total positive BASE contribution <= 40%.

Observed maximum single-trade positive-contribution share: **53.9646%**.

## Official decision

Final V2 classification after the prospectively frozen 2025 independent OOS:

**TIER 3 — WATCHLIST / NEAR-DIAMOND CANDIDATE REMAINS**

The candidate is **not** promoted to `TIER 2 — PROMOTED CANDIDATE / QUASE DIAMANTE` because the prospectively frozen concentration gate failed. The positive 2025 OOS economics are real evidence and materially strengthen the mechanism, but one winning trade contributes too much of total positive BASE PnL for Path 2 promotion under the frozen protocol.

No post-outcome event deletion, threshold adjustment, horizon change, cost change, pair change, subgroup selection, stop/target overlay, or 2026 rescue is authorized.

## Governance

- live trading: **NO**
- exchange mutation: **NO**
- orders: **NO**
- merge to main: **NO**
- deployment: **NO**
- 2026 market access: **NO**
- post-outcome rescue: **NO**
