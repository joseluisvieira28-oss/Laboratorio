# V04B — SOURCE-TIMEZONE SCHEMA AMENDMENT BEFORE FUNDING OUTCOMES

UTC 2026-10-19. **This is strictly a source-format / timestamp-boundary repair**, not a modification to the already-frozen strategy, source assets, costs, signal threshold, fixed 28 daily entry/exit days or interpretation of profitability.

## Observed schema blocker

Original first publisher-rate source attempted via immutable two ZIP links, but the reader failed BEFORE parsing the numerical funding_rate because the publisher June-2025 BTC-USDT archive contained one `funding_time` parsed in UTC as **2025-05-31T16:00:00Z**. [Failed original 2025 source diagnosis GitHub run 39242064119](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39242064119). This time is exactly **2025-06-01 00:00 in UTC+08:00**, consistent with an Asian-local publisher date grouping. No payout values, return scores or statistical outcomes were computed during the failure; all tests Windows/Linux passed.

### Frozen repair before outcome data

- The **source archive membership envelope ONLY** is expanded to `2025-05-31T16:00:00.000Z <= observed settlement_time < 2025-06-30T16:00:00.000Z`, exactly June 2025 in UTC+08. This is NOT permission to include any extra May outcome or July settlement in a trading episode.
- Original evaluation is unchanged, still `2025-06-02 00:05Z` to `2025-06-30 00:05Z`, 28 non-overlapping entries June02..June29 inclusive, 24h horizon; every settlement strictly inside each corresponding interval. Do not shift signal timestamps or move calendar day to accommodate favorable outcomes.
- Preserve actual physical UTC timestamp and explicit original timezone if available, never strip/relabel a settlement; do not treat it as occurring June1 UTC if actually May31 16Z.
- **Deny** rows outside this exact UTC+8 archive month envelope, duplicated/out-of-order time, unsupported 1h/4h/8h gap, wrong instrument, missing markPx (the economic full source gate remains blocked), and missing observation for any episode.
- Tests MUST add exact UTC+8 boundary fixtures, including 2025-05-31T16:00Z accepted when valid local June, 2025-06-30T16:00Z rejected (local July1), and original UTC 28 entry days unchanged. Run source after test passes.
- The previous V04 frozen 30/50bps cost hurdle, >=0.5bps/hour ex-ante prior two settlements, no asset selection, funding sign, no actual cashflow, no OOS credit, no trading authority, no live orders, no 2026 holdout remain identical.

**Interpretation of evidence:** this amendment was committed after reviewing only a timestamp-format error, not any observed funding rates. It is transparent, not an outcome-optimized economic rule. If another format anomaly appears, stop and document it rather than reclassify outcomes.
