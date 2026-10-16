# LICP ATTACK STATUS — 2026-10-08

## Canonical LICP-001 primary forward

Scientific authority:
- BTC_CONFIRMED
- target BTC_USDT
- 60s primary horizon
- continuation direction
- 16 bps base taker/taker cost
- 32 bps stress
- first 20 independent episodes
- >=3 UTC dates
- >=90% primary coverage

Mandatory eligible historical-forward receipt:
- run 37311668666
- artifact 11364886047
- artifact SHA256 dbf6cc1cf8a8f22d556d7adf7cf475ed14f58747d1ac45b83bc67a5280ad8f39
- 6 BTC_CONFIRMED primary events
- 6/6 complete BTC_USDT 60s outcomes
- one UTC date
- mean gross +3.1487 bps
- mean base net -12.8513 bps
- median base net -13.9378 bps
- mean 2x-cost net -28.8513 bps
- state: FORWARD_INSUFFICIENT

Current collection attacks:
- run 37731550461 — durable V0.1 shard — queued
- run 37732298106 — durable V0.2 with mandatory baseline restore — pending

No terminal edge verdict is authorized at N=6.

## Historical survivor transfer — LICP-FWD-XALT-004

Frozen candidate:
- confirmed BTC SELL liquidation ignition
- target MEXC SOL_USDT
- wait 60s after confirmation
- SHORT
- exit after 60 minutes
- 16 bps taker hurdle
- >=20 episodes
- >=3 UTC dates
- <=10% missing

Canonical live forward state:
- run 37309426462
- artifact 11364180883
- artifact SHA256 3e819c369a1ce01769f5f678bddc95856277a5877bfceed03621468cb2f46e3a
- matured/completed 4/4
- missing 0
- one UTC date
- event net bps: +23.1504, +10.7782, -5.0994, -74.0124
- mean net -11.2958 bps
- median gross +18.8394 bps
- state: FORWARD_INSUFFICIENT

Current continuation:
- run 37732159597 — durable state-restoring XALT-004 continuation — queued

Historical XALT-003 holdout remains separate and survives historically. It cannot rescue a failed live transfer verdict.

## Integrity hardening

Durable canonical LICP sharding now:
- preserves immutable shard receipts;
- restores mandatory eligible run 37311668666;
- reconstructs legacy episode IDs only from the frozen tuple config_version | ignition_ts | pressure;
- deduplicates by deterministic episode ID;
- fails closed on conflicting duplicate content;
- preserves observation gaps;
- never backfills missing outcomes after restart.

## Governance

Research only.
No orders.
No authentication.
No account reads.
No exchange mutation.
No wallets/capital.
No main merge.
No post-outcome tuning.
