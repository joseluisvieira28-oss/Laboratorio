# LL-0017-TPD-001 — Top-vs-Global Positioning Divergence

State: **FROZEN PRE-DISCOVERY / SOURCE GATE PASS / 2024H1 CONFIRMATION LOCKED**.

This child recovers the explicit LL-0017 IDEA ONLY follow-up after LL-0016-C formally closed NO EDGE.

## Material distinction

This is not a rescue of LL-0016-C and not another taker-flow lab.

- LL-0016-C tested extreme funding + expanding OI crowd unwind and closed NO EDGE.
- SCL-AGG-002 tested generic aggressive taker flow and closed NO EDGE with 0/240 survivors.
- LL-0017-TPD-001 uses a participant-class positioning divergence not previously executed in the repository: position-weighted TOP trader L/S ratio versus GLOBAL account-count L/S ratio.
- Funding and OI are excluded from the primary.
- Taker ratio is diagnostic only and cannot rescue the primary.

## Frozen primary

D_t = ln(sum_toptrader_long_short_ratio) - ln(count_long_short_ratio).

Causal 30-calendar-day z-score, current row excluded, minimum 99% 5m coverage.

A new event occurs only when z crosses +1.5 or -1.5:
- +1.5 cross => LONG;
- -1.5 cross => SHORT.

Execution:
- source metrics 5m UTC;
- entry +5m at 1m open;
- primary hold 60m;
- one active event per asset;
- 14 bps base and 20 bps stress round-trip costs.

Universe: BTC, ETH, SOL, BNB, XRP, DOGE USD-M perpetuals.

## Temporal firewall

- January 2023: causal warm-up only.
- Discovery scored: 2023-02-01 through 2023-12-31.
- 2024-01-01 through 2024-06-30: locked Confirmation.
- 2024H2 untouched.
- 2025 locked.
- 2026 locked.

## Source receipt

3,282 official daily/metrics archives for 2023 through 2024H1 were independently re-hashed for LL-0017; 3,282/3,282 matched provider CHECKSUM. The four positioning/taker fields have >=99.985% coverage in every asset over that eligible period.

The 2023 price package contains 72 official monthly 1m archives; 72/72 checksum PASS, 525,600 minutes per asset, 100% coverage and zero duplicate open timestamps.

## Decision

Exactly one primary cell. All frozen gates must pass. 30m/120m, top-account divergence and taker ratio are diagnostics only.

A Discovery survivor is **not** an edge, candidate or promotion. It only makes a separately frozen 2024H1 confirmation eligible.

No live trading, exchange mutation, alerts, wallets, leverage or main merge.
