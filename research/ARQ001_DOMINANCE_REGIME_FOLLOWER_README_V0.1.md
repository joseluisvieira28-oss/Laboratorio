# ARQ-001-DRF-001 — Dominance-Regime Conditioned BTC→ALT Residual Follower

## State

PRE-DISCOVERY FROZEN / SOURCE GATE BLOCKED / OUTCOMES UNOPENED.

This branch recovers the strongest unfinished lineage from the Lost Edge Archaeology audit. It does not reopen H180, LL-0004, Family E, F08 or any closed hypothesis.

## Material distinction

Already-tested families answered different questions:

- H180: simple BTC→ALT hourly lead-lag.
- LL-0004: BTC-factor residual mean-reversion/continuation.
- Family E: raw cross-sectional relative strength.
- F08: factor-adjusted cross-sectional residual ranking.
- Queue06 F07 audit: recognized prior BTC-triggered ALT rotation/dominance work but did not execute this exact contract.

ARQ-001 asks a narrower incremental-information question:

Given a frozen BTC + residual follower signal, do BTC.D, USDT.D and TOTAL3 regime variables prospectively identify a subset with better subsequent ALT returns after costs?

## Frozen legacy defaults

- Binance USD-M Futures 1m.
- BTC trigger; ETH/SOL/BNB/XRP/DOGE followers.
- Top of UTC hour.
- Observe HH:00, HH:01, HH:02 only.
- Enter HH:03:00.
- BTC absolute z >= 0.75.
- Backward-looking beta: 30 days.
- ALT residual absolute z >= 1.0.
- Primary horizon: 5m.
- Diagnostic horizons: 1m / 3m / 10m / 15m.
- No stop/TP in Discovery.
- 1x notional.
- Nested ablation A -> B -> C -> D.
- Regime D long: BTC.D down, USDT.D down, TOTAL3 up.
- Regime D short: BTC.D up, USDT.D up, TOTAL3 down.
- Cost bands: 10 / 12 / 14 bps round trip.

## Governance modernization frozen before outcomes

- Discovery: 2022-2024 only.
- 2025: locked Confirmation.
- 2026: locked Final Holdout.
- A Discovery survivor is not an edge and only becomes eligible for a separately frozen 2025 Confirmation.
- No live trading, alerts, wallets, exchange mutation, leverage, or main merge.

## Current blocker

The Binance leg can potentially reuse checksum-audited historical 1m authority, but no authoritative historical BTC.D.csv, USDT.D.csv, or TOTAL3.csv was recovered in Drive, Library or GitHub.

The legacy research explicitly required TradingView CRYPTOCAP CSV exports and rejected unofficial scraping as a production/source substitute.

Therefore the correct current state is SOURCE_GATE_BLOCKED — NOT NO_EDGE.

No market outcome is authorized until all three regime series are present, timestamp semantics are audited, coverage is sufficient for 2022-2024, and a deterministic loader is frozen.

## Next action

Acquire/export only the three frozen TradingView regime series, perform a metadata/coverage/schema audit, freeze their checksums and synchronization semantics, then implement the real data runner. Do not inspect ARQ-001 returns before that source receipt exists.
