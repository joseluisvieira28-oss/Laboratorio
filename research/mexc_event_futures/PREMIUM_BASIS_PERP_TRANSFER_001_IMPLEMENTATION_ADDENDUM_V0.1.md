# PREMIUM-BASIS-PERP-TRANSFER-001 — IMPLEMENTATION ADDENDUM V0.1

Freeze commit: `c0b402ac658974a944d42c62bd888a07db35bfd2`
Freeze commit timestamp: **2026-10-08T05:47:49Z**

That timestamp is the immutable no-backfill boundary.

Current official public Futures API domain: `https://api.mexc.com`.

Public endpoints used:
- index Min5: `GET /api/v1/contract/kline/index_price/MUSTOCK_USDT`
- fair Min5: `GET /api/v1/contract/kline/fair_price/MUSTOCK_USDT`
- depth: `GET /api/v1/contract/depth/MUSTOCK_USDT`

Initial transport/source gate:
- 630 seconds;
- depth poll every 30 seconds;
- >=20 healthy non-crossed snapshots;
- observed span >=600 seconds;
- at least one successful index and fair-price warmup retrieval with enough data to construct the frozen 24h z-score;
- outcomes opened: 0.

No scientific rule in the parent freeze is changed.
