# Rejected or Non-Authoritative Sources

## Rejected as primary evidence

- **Current BLS/FRED series:** may contain later revisions and cannot establish the
  first-release value or release clock.
- **Post-release Reuters/AP/MarketWatch articles as sole consensus evidence:** they can
  state what a poll predicted, but the accessible artifact itself is after T0.
- **CME FedWatch:** measures policy-rate probabilities, not economist consensus for CPI or
  Employment Situation fields.
- **Search snippets and AI summaries:** mutable, incomplete and not the source payload.
- **Undated or date-only same-day research:** cannot prove availability before 08:30 ET.
- **Reconstructed consensus:** averages assembled after the event, inferred values and
  reverse-engineered forecasts are hindsight-contaminated.

## Discovery only unless independently snapshotted before T0

- Investing.com historical calendar
- Forex Factory historical calendar
- Trading Economics current historical calendar/API response
- Econoday public mirrors
- Nasdaq economic calendar
- Yahoo Finance calendar
- GitHub and Kaggle compilations

These may locate events or corroborate values, but current pages can be overwritten,
revised or re-rendered without a historical version timestamp. A pre-T0 Wayback capture
of the exact page may upgrade that individual artifact to `USABLE_WITH_CONTROLS`; it does
not upgrade the platform globally.

## Premium source note

Bloomberg and commercial Reuters survey feeds are likely the strongest structured route
because they can preserve survey timestamps, medians and contributors. They were neither
purchased nor accessed. A future licensed route must still preserve vendor snapshots and
terms; premium status alone is not proof of point-in-time correctness.
