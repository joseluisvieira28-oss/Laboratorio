# LICP-001 — FORWARD DURABLE SHARDING ADDENDUM V0.1

Date: 2026-10-08
Status: OPERATIONAL HARDENING ONLY / SCIENCE UNCHANGED
Branch: `liquidation-cascade-propagation-v0.1`

## Purpose

Make the already-frozen LICP-001 forward observation durable across bounded GitHub Actions
shards without changing any scientific rule.

Canonical scientific authorities remain:
- `LICP_001_TRIGGER_CONFIG_V0_1.json`
- `LICP_001_PROPAGATION_OUTCOME_PROTOCOL_FREEZE_V0_1.md`
- `LICP_001_FORWARD_ECONOMIC_VERDICT_FREEZE_V0_1.md`

## Sharding rule

A forward observation may be split into bounded runtime shards.

Shard duration is an operational property only. It does NOT change:
- Bybit BTC ignition threshold;
- Binance confirmation threshold;
- same-pressure rule;
- 120-second episode cooldown;
- target venue or symbols;
- 1/2/5/15/30/60-second horizons;
- continuation direction;
- 16 bps base taker/taker hurdle;
- 32 bps stress hurdle;
- first-20 verdict sample;
- >=3 UTC-date requirement;
- >=90% primary-outcome coverage requirement.

The first eligible BTC_CONFIRMED episodes are determined by frozen ignition timestamps across
all eligible post-freeze receipts, not by shard boundaries.

## Persistence and restart semantics

Each shard is immutable evidence.

A durable ledger may aggregate prior shard artifacts only when:
- receipt status is `FORWARD_OBSERVATION`;
- `live_trading == false`;
- trigger-config version and SHA-256 match the current frozen config;
- the receipt began after the canonical economic-verdict freeze;
- every record has a deterministic `episode_id`.

Deduplication:
- identical duplicate episode IDs are retained once;
- same episode ID with conflicting record content => `BLOCKED_INTEGRITY_CONFLICT`.

Restart/gap handling:
- wall-clock gaps between shards are preserved in the ledger;
- no event is inferred inside a gap;
- no missing 60-second outcome is backfilled from later market data;
- an episode whose required primary horizon was not captured remains incomplete and counts
  against the frozen coverage rule if it falls in the first 20.

No overlapping transport may create multiple scientific episodes. The deterministic episode ID
and the frozen 120-second cooldown remain authoritative.

## Current attack shard

The 2026-10-08 operational attack uses a 600-second bounded shard so that transport,
persistence, deduplication, and the current forward state can be adjudicated immediately.

This does not establish a new sample-size rule and does not replace longer future observation
blocks.

## Governance

Public data only.
No orders.
No authentication.
No exchange mutation.
No wallets/capital.
No main merge.
No threshold/horizon/target/cost tuning.
