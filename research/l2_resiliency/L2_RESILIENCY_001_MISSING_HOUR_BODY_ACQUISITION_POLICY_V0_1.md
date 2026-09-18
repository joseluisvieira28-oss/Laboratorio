# L2-RESILIENCY-001 — Missing-Hour & Body-Acquisition Policy V0.1

Date: 2026-09-18
Status: FROZEN PRE-OUTCOME / SOURCE-ONLY

## Inventory result
The exact 2024 BTC hourly-key census adjudicated all 8,784 frozen keys:
- PRESENT: 8,707
- MISSING: 77
- ERROR: 0
- EMPTY PRESENT: 0
- coverage: 99.1234061931%
- present compressed bytes: 6,832,137,900 (6.362924259 GiB)

The 77 missing hours are source facts, not a parameter to optimize.

## Frozen missing-data rule
1. No missing hourly object may be replaced by another venue, vendor, asset, reconstructed book, interpolation, forward fill, backfill, synthetic snapshot or adjacent-hour proxy.
2. Discovery may use only official BTC l2Book records contained in successfully acquired PRESENT 2024 objects from the frozen inventory.
3. Hourly objects form contiguous source segments only when their UTC hours are adjacent and both objects are PRESENT.
4. A sweep candidate is eligible only when:
   - its pre-sweep and sweep-transition snapshots are inside the same contiguous source segment; and
   - every required +1s, +5s, +15s replenishment observation and the maximum +60s midpoint-response horizon can be resolved inside that same contiguous source segment.
5. Any candidate whose required window touches/crosses a missing-hour boundary is excluded mechanically before its outcome is evaluated.
6. No rule, threshold, depth-level count, horizon or event direction may be altered because of the missing pattern.
7. The exact missing-key ledger remains immutable provenance.

## Body-acquisition gate
Acquire exactly the 8,707 keys classified PRESENT by the frozen inventory.

For every object:
- RequestPayer=requester.
- GET exact key only.
- preserve raw .lz4 bytes;
- GET ContentLength must equal inventory ContentLength;
- GET ETag must equal inventory ETag;
- compute and persist SHA256;
- no decompression during acquisition;
- no 2025/2026 request;
- fail closed on unexpected key, ETag, size, authentication error or download failure.

### SOURCE_BODY_PASS
Requires:
- 8,707/8,707 PRESENT keys successfully acquired or locally verified from this acquisition corpus;
- exact inventory key set match;
- zero extra keys;
- zero size/ETag mismatches;
- SHA256 recorded for every raw object;
- byte-total exactly 6,832,137,900 unless a remote-object metadata change is detected, in which case fail closed and investigate provenance;
- protected-period and no-outcome firewalls PASS.

Body acquisition does NOT authorize Discovery. After SOURCE_BODY_PASS, a separate source-body parsing/schema audit must pass before event construction.

## Outcome firewall
During inventory/body acquisition:
- no decompression except later explicit schema audit;
- no sweep events;
- no replenishment ratios;
- no midpoint responses;
- no returns/PnL;
- no 2025/2026;
- no live trading/exchange mutation.
