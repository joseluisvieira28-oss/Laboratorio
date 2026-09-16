# TFG-EMA-PULLBACK-1D-BINANCE-PREPERIOD-001 — Closeout V0.1

Date: 2026-09-16

## Terminal classification

**INSUFFICIENT_SAMPLE**

This is not a formal NO_EDGE / REPLICATION_FAIL classification because the prospectively frozen minimum was 100 resolved trades and this independent replication produced only 11 resolved trades.

The descriptive economics are nevertheless materially adverse and must not be hidden or reinterpreted:

- resolved trades: **11**
- selected trades: **12**
- raw triggers: **15**
- BASE net expectancy: **-0.4687603633 R/trade**
- BASE profit factor: **0.4270706671**
- BASE win rate: **18.18%**
- BASE median: **-1.0 R**
- fixed-cohort STRESS net expectancy: **-0.4755824097 R/trade**
- fixed-cohort STRESS profit factor: **0.4187326104**
- 95% UTC-day block-bootstrap interval: **[-1.0000000000, +0.3266477265] R**
- bootstrap sample days: **11**
- target reach: **18.18%**
- symbol distribution: BNB 4, DOGE 1, ETH 1, XRP 5; BTC 0, SOL 0

## Source / continuity audit

Provider: Binance Data Vision public Spot monthly 15m klines.

Frozen source period: 2021-01-01 inclusive to 2023-01-01 exclusive. No 2023, 2024, 2025 or 2026 data were accessed.

- checksum-verified monthly archives accepted: **144 / 144**
- prospectively amended noncanonical-close sanitation: reject row, never retime/interpolate/synthesize/backfill
- noncanonical close-time rows rejected: **23**
- derived complete UTC daily bars: BNB 723, BTC 723, DOGE 723, ETH 723, SOL 723, XRP 724
- incomplete UTC daily buckets dropped: **41 total**
- detected daily continuity gaps: **41 total**
- contiguous daily segments: **47 total**

The exact inherited EMA engine resets indicator state at each continuity segment. This is required by the frozen complete-bucket / split-continuity rule. The fragmentation materially reduced the number of eligible signals, but no post-outcome bridging, backfill, extension, or alternate indicator initialization is permitted.

## Scientific interpretation

The parent MEXC 2023-2024 Discovery was also formally `INSUFFICIENT_SAMPLE` with 71 resolved trades, but descriptively positive (+0.1538061081 R BASE, PF 1.2689763; +0.1325433127 R STRESS).

This independent Binance 2021-2022 non-overlapping robustness replication is descriptively negative (-0.4687603633 R BASE, PF 0.4270706671), with only 11 resolved observations.

Therefore:

1. This result **does not formally reject** the EMA Pullback 1D geometry because the frozen n>=100 adjudication gate was not met.
2. It **does materially weaken confidence** in temporal/venue robustness. The observed sign reversal is adverse evidence, even though the sample is too small for formal economic adjudication.
3. The 11 new observations must **not** be pooled with the parent's 71 to manufacture 82 trades or to reinterpret the minimum-100 gate.
4. No opportunistic period extension, parameter change, filter, asset selection, source repair, 2025 access, or 2026 access is authorized.
5. No shadow/live promotion is authorized from this result.

## Governance

- research-only: PASS
- fail-closed: PASS
- 2023 access: false
- 2024 access: false
- 2025 access: false
- 2026 access: false
- exchange mutation: false
- orders: false
- alerts/webhooks: false
- merge to main: false
- post-outcome tuning: false
- rescue: false
- terminal stop: true

## Canonical execution

GitHub Actions run: `35134419519`

Execution HEAD: `9209ca6850a94b6bc41db21c480bfd82df810ece`

Closeout artifact ID: `10462162542`

Closeout artifact digest: `sha256:6fd215a4f92ceb1f1970d6c32edb3a5f8b67bc439567cda2365e986b540549ba`

Source artifact ID: `10462062546`

Source artifact digest: `sha256:190126bf037b3cdeb391aac8428d35950c2aaa4a8751776d7b591e9ac2cf7986`

Closeout JSON self-excluded SHA-256: `a16c86341e5cb1e093c1d496fcd54fb3ce0a77a3b2c29b2fff8a12ef9d8e35fe`

Ledger SHA-256: `fafcfb4caf88efb5909ed06b84c1cc50d813794a75592aa28700462b51f81745`

## Stop rule

The exact `TFG-EMA-PULLBACK-1D-BINANCE-PREPERIOD-001` replication is terminal. Any materially different future replication requires a new prospective authority before accessing outcomes.
