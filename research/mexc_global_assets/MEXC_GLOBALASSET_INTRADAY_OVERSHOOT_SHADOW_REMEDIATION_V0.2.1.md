# MEXC GLOBAL-ASSET INTRADAY OVERSHOOT — SHADOW V0.2.1 TECHNICAL REMEDIATION

Date: 2026-10-05
Status: TECHNICAL REMEDIATION ONLY — SCIENCE UNCHANGED

Authority remains exactly MEXC_GLOBALASSET_INTRADAY_OVERSHOOT_SHADOW_FREEZE_V0.2.md.
No signal, universe, threshold, direction, horizon, cost scenario, notional bucket, minimum sample,
or PASS/FAIL criterion is changed.

Corrections:
- LATE_SCAN now fails closed for that minute instead of scoring stale historical candles and capturing a current book.
- per-segment state is durably checkpointed using atomic JSON replacement.
- processed timestamps are deduplicated on restart.
- the frozen 10-minute global cooldown is enforced online within the durable segment state.
- missing/invalid contractSize fails closed; there is no silent default to 1.
- entry book is rejected when capture age exceeds 45 seconds from the frozen signal timestamp.
- workflow branch binding points to the remediation branch.

Known remaining limitation:
Cross-segment/global-day cooldown and aggregation still require a durable cross-segment aggregator.
Therefore no operational PASS may be issued from isolated segment receipts alone.
The frozen minimum remains >=30 admitted event baskets and >=5 distinct session dates.

No outcomes were opened by this remediation commit.
No private endpoints, account reads, orders, wallets, exchange mutation, or live trading.
