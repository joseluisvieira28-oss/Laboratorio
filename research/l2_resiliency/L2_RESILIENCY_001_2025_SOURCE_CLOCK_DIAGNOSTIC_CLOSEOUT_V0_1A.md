# L2-RESILIENCY-001 — 2025 SOURCE CLOCK DIAGNOSTIC CLOSEOUT V0.1A

Date: 2026-09-23
Status: **SOURCE_CLOCK_DIAGNOSTIC_COMPLETE / MIXED_FUTURE_PAYLOAD_SEMANTICS_REQUIRES_REVIEW**
Scope: source/timestamp only. No sweep, replenishment, midpoint-response, return, PnL or 2026 outcome access.

## Canonical binding

- official Hyperliquid BTC l2Book 2025 objects: 8,400
- compressed bytes: 8,975,275,014
- contiguous PRESENT segments: 3 = 6,923 + 613 + 864 hours
- canonical manifest SHA256: `767e75594864344c75dd2669ec4fad8c738710c218322b11fd43a83077ef17c3`
- RAW corpus was reconstructed from the byte-preserving Drive backup and all three archive SHA256 values matched their frozen manifests before this diagnostic.

## Full-corpus result

- records: 53,647,758
- future payload rows: 109
- future <=1ms: 9
- future >1ms: 100
- future rows matching floor-ms + 1 quantization: 9 / 109 = 8.2568807339%
- future ahead, ceil microseconds:
  - min: 146
  - median: 6,539
  - p95: 27,005
  - p99: 35,153
  - max: 42,610
- payload backwards: 171
- payload equal: 13,925
- envelope backwards: 0
- envelope outside key hour: 0
- parser/schema fallback: 0

The 109 future rows are concentrated in 14 UTC dates in January 2025; none were observed after 2025-01-25 in this corpus.

## Frozen routing

The previously authorized routing is therefore:

`MIXED_FUTURE_PAYLOAD_SEMANTICS_REQUIRES_REVIEW`

The complete-sub-1ms quantization route does **not** apply because 100 / 109 future rows exceed 1ms and the maximum observed lead is 42.609667ms.

This is not NO_EDGE and not a validation outcome.

## Equivalence audit

The optimized full-corpus source-clock executor was checked against the canonical V0.1A runner on a deterministic first-24-hour slice:

- records: 150,718 / 150,718
- future rows: 9 / 9
- future <=1ms: 3 / 3
- future >1ms: 6 / 6
- all future-ledger fields: exact row-for-row match
- schema fallbacks: 0

## Evidence hashes

- diagnostic receipt SHA256: `0472ff0f69623442b8fb16ba795cc3615aef6a6e0fe906b867b8084a1955c178`
- future ledger SHA256: `bc183c8e2206f30626fe213955b47c29ec9281f0eec9ab4fce476693f1cccc2b`
- object audit SHA256: `079fbaa532408e715f6ef892519951ad1e040b98c4ea30906e36cd7a8b8cda20`
- evidence bundle SHA256: `16c397f1942733e43e6b374d530dbd41097427d83cd34af304246dc0c41f5363`

## External source semantics check

Hyperliquid's official documentation confirms that the nested l2Book response has a millisecond `time` field and that historical l2Book snapshots are distributed in the official requester-pays S3 archive. The public documentation reviewed does not assign an authoritative economic meaning to the outer archive envelope `time` field.

Therefore this closeout does not invent a provider claim about cross-clock causality.

## Next gate

A source-only normalization amendment may be frozen prospectively because no 2025 sweep/replenishment/response outcome has been opened.

Any amendment must:
- preserve the frozen envelope-order/event-anchor rule;
- preserve raw payload timestamps without clamping;
- introduce no fitted numeric clock-skew threshold;
- preserve the existing stale-late quarantine rule;
- prove exact 2024 equivalence where the future-payload branch is never invoked;
- be implementation-locked before 2025 validation outcomes are reopened.

## Firewalls

- 2025 validation outcome opened: false
- 2026 accessed: false
- PnL/costs/Sharpe: false
- live trading/orders/exchange mutation: false
- main merge: false
