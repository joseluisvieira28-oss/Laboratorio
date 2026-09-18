# L2-RESILIENCY-001 — 2024 BTC OFFICIAL ARCHIVE ACQUISITION PLAN V0.1

Date: 2026-09-18
Status: FROZEN SOURCE-ONLY PLAN / NO OUTCOMES

## Upstream evidence
Recovered user-supplied HL_RUN02 bytes were hash-verified. Exact official object:
- s3://hyperliquid-archive/market_data/20240901/0/l2Book/BTC.lz4
- SHA256 5c8f66e5215deb7dc46f436dd997d299593a090b3a65a9cc9b6f642765aec2ec
- 6,277 valid snapshots in one hour
- zero invalid records, duplicate timestamps or backwards timestamps
- top-5 depth structurally complete on all records
- +1s/+5s/+15s follow-up clocks structurally observable

Classification: L2_SOURCE_SCHEMA_AND_CLOCK_PREFLIGHT_PASS_PARTIAL_COVERAGE.

## Frozen target
Asset: BTC only.
Dataset: Hyperliquid official historical archive market_data/l2Book.
Calendar: 2024-01-01 through 2024-12-31 UTC inclusive.
Hours: 0..23 for every UTC date.
Expected exact key population: 366 * 24 = 8,784 hourly object keys.
Key rule:
market_data/YYYYMMDD/H/l2Book/BTC.lz4

No ETH. No 2025. No 2026. No alternate venue. No alternate vendor. No pseudo-L2 reconstruction.

## Gate A — exact-key inventory only
Execute HEAD against exactly 8,784 frozen keys with RequestPayer=requester.
Persist only:
- key
- exists / missing / error
- ContentLength
- ETag
- LastModified
- HTTP/error class

Do not GET object bodies in Gate A.
Do not decompress.
Do not compute sweep events.
Do not compute replenishment.
Do not compute midpoint response, returns or PnL.

### Inventory PASS
SOURCE_INVENTORY_PASS requires:
- all 8,784 exact keys adjudicated;
- zero ambiguous/auth failures;
- every present object's size > 0;
- exact missing-key list preserved;
- protected-period firewall PASS.

Because Hyperliquid explicitly does not guarantee completeness, missing objects are reported, never silently replaced.

## Gate B — body acquisition
Dormant until Gate A receipt is reviewed and a requester-pays byte/cost ceiling is explicitly authorized.
If activated:
- 12 calendar-month shards;
- exact keys only;
- RequestPayer=requester;
- byte-preserving .lz4;
- SHA256 per object;
- no decompression in acquisition;
- no 2025/2026;
- fail closed on unexpected key/size/auth behavior.

## Scale estimate
The verified 2024-09-01 00 BTC object is 690,391 compressed bytes.
Naive 8,784-hour extrapolation is ~6.06 GB decimal (~5.65 GiB), but this is planning-only; Gate A exact ContentLength census controls the real byte ceiling.

## Discovery remains locked
No L2-RESILIENCY-001 event or outcome computation is authorized by this plan.
