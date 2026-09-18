# L2-RESILIENCY-001 — Full-Corpus Structural Schema Audit V0.1

Date: 2026-09-18
Status: FROZEN PRE-OUTCOME / SOURCE-SCHEMA ONLY
Prerequisite: SOURCE_BODY_ACQUISITION_PASS (8,707/8,707 objects; 6,832,137,900 bytes).

## Scope
Exact corpus: the 8,707 BTC / 2024 Hyperliquid official l2Book objects in the frozen acquisition manifest.
The 77 inventory-MISSING hours remain absent and immutable. No alternate source, interpolation or reconstruction.

## Per-object byte binding
Before decompression every object must match the frozen manifest:
- exact key/path;
- exact byte size;
- SHA256;
- MD5 / ordinary S3 ETag.

Any mismatch fails closed for the full audit.

## Structural record contract
Every decompressed non-empty line must be valid JSON and satisfy:
- top-level time, ver_num, raw;
- raw.channel == l2Book;
- raw.data.coin == BTC;
- raw.data.time is an integer millisecond timestamp;
- exactly two levels side arrays;
- each side has at least five levels;
- each of the first five levels has parseable positive px, non-negative sz, and integer non-negative n;
- first five bid prices strictly descend;
- first five ask prices strictly ascend;
- best bid < best ask.

## Time contract
- data timestamps must be non-decreasing within each object;
- no backwards timestamp is permitted;
- every data timestamp must fall inside the UTC hour encoded in that object's frozen key;
- first/last timestamp and record count are persisted per object;
- duplicate timestamps are reported, not silently removed.

## Source segmentation
Contiguous source segments are defined only by adjacent PRESENT hourly keys.
The 77 MISSING keys split segments mechanically.
This audit records segment boundaries only. It does not construct sweep events.

## PASS
SOURCE_SCHEMA_PASS requires:
- 8,707/8,707 raw objects byte-bound to the manifest;
- 8,707/8,707 objects decompress successfully;
- zero JSON/schema violations;
- zero wrong coin/channel records;
- zero timestamps outside their frozen hour;
- zero backwards timestamps;
- zero top-5 structural violations;
- zero crossed books in validated top-of-book;
- no 2025/2026 access.

Duplicate timestamps, if any, are preserved and counted. They do not by themselves fail this source gate unless they conflict with the frozen time/order contract.

## Firewalls
Forbidden in this audit:
- sweep-event construction;
- replenishment ratios;
- weak/strong replenishment labels;
- midpoint response/direction;
- returns/PnL/PF/win rate/drawdown;
- signal thresholds;
- 2025/2026;
- live trading/orders/wallets/exchange mutation.

Passing this gate proves only that the raw 2024 L2 corpus is structurally usable. Discovery remains separately gated.
