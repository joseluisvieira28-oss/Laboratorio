# FUNDING-SHOCK-RESET-001 — PRE-OUTCOME FREEZE V0.1

Date frozen: 2026-10-05
Branch: `funding-shock-reset-v0.1-prereg-2026-10-05`
Status at freeze: PRE-OUTCOME / RESEARCH-ONLY

## Question

Does a mechanically crowded perpetual market snap back after funding settlement when BOTH:

1. the just-settled Binance USD-M funding rate is extreme in the same direction as crowding; and
2. the final pre-settlement hour of futures price action moved in that same direction?

The test intentionally enters only AFTER settlement. It never attempts to collect the funding payment itself.

## Economic mechanism

Perpetual funding transfers cash between long and short holders and exists to force convergence between the perpetual contract and its underlying index/spot. Extreme positive funding indicates longs paying shorts; extreme negative funding indicates shorts paying longs. If the final pre-settlement hour also chases in the same direction, the hypothesis is that the crowded side partially unwinds after the forced cash transfer.

## Public/free authority

Primary source: Binance public Data Vision USD-M archives.

Klines:
`https://data.binance.vision/data/futures/um/monthly/klines/{SYMBOL}/5m/{SYMBOL}-5m-{YYYY-MM}.zip`

Funding:
`https://data.binance.vision/data/futures/um/monthly/fundingRate/{SYMBOL}/{SYMBOL}-fundingRate-{YYYY-MM}.zip`

Every downloaded archive must have its official `.CHECKSUM` sidecar verified. Any checksum failure is SOURCE_BLOCKED.

## Frozen universe and dates

Symbols:
- BTCUSDT
- ETHUSDT

Research window:
- 2021-01-01 00:00:00 UTC through 2025-12-31 23:59:59 UTC.

Hard exclusion:
- ALL 2026 data.
- No live/private endpoints.
- No account, balance, wallet, order, position or exchange mutation.

## Frozen signal

At funding settlement time T0:

- Extreme funding threshold: `abs(funding_rate) >= 0.0005` (0.05% per settlement).
- Pre-settlement momentum threshold: `abs(pre_60m_return) >= 0.005` (0.50%).
- Alignment required:
  - positive funding AND pre_60m_return >= +0.50% => SHORT signal;
  - negative funding AND pre_60m_return <= -0.50% => LONG signal.
- Otherwise: NO SIGNAL.

No threshold optimization is permitted after outcomes are opened.

## Frozen timestamps / anti-lookahead

Pre-60m return uses only the final completed 5m close immediately before T0 and the completed 5m close exactly 60 minutes earlier.

Entry is delayed to the OPEN of the 5m bar at T0 + 5 minutes.

This 5-minute buffer is intentionally conservative and prevents using the funding timestamp bar as an executable hindsight price.

Primary exit is exactly 4 hours after entry, using the close of the corresponding completed 5m bar.

Secondary 1h and 8h exits are descriptive mechanism checks only and CANNOT rescue or promote the family.

## Frozen direction

Always fade the crowded side:
- positive funding aligned with positive pre-momentum => SHORT;
- negative funding aligned with negative pre-momentum => LONG.

FOLLOW vs FADE may not be chosen after opening outcomes.

## Frozen primary statistic

To prevent BTC/ETH same-timestamp correlation from double-counting evidence, the primary series is an equal-weight EVENT PORTFOLIO by funding timestamp:
- if one symbol fires, use that symbol;
- if both fire, average their signed strategy returns.

Primary horizon: 4h.

Primary friction stress: subtract 8 basis points round-trip from every event-portfolio return.

## Frozen survival gate

`SURVIVES_V0.1` requires ALL:

1. Source integrity PASS, including checksum verification.
2. At least 40 distinct primary event timestamps.
3. Mean 4h gross event-portfolio return > 0.
4. Mean 4h net return after 8 bps round-trip friction > 0.
5. 95% block-bootstrap lower confidence bound of mean 4h net@8bps > 0.
6. Net@8bps total return positive in every chronological third.
7. BTC-only and ETH-only 4h gross mean returns are both > 0, provided each has at least 10 signals.
8. Zero use of 2026 outcomes.
9. Zero post-outcome rule changes.

If any scientific gate fails: `NO_EDGE_V0.1`.
If source/timestamp integrity fails: `SOURCE_BLOCKED_V0.1`.

## Bootstrap

Fixed seed: 20261005.
10,000 bootstrap resamples of UTC calendar-day blocks from the primary event portfolio.

## Economic diagnostics (non-promotional)

Report:
- N signals by symbol and year;
- mean/median/win rate at 1h, 4h, 8h;
- gross 4h return;
- net 4h under 4/8/12 bps round-trip friction;
- break-even round-trip friction in bps;
- chronological-third results;
- positive-funding vs negative-funding subsets.

These diagnostics cannot alter the frozen verdict.

## Governance

Research only. No live trading. No merge to main. No exchange mutation. No post-outcome tuning. A new version requires a new pre-outcome freeze and untouched future data.
