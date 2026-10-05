# BINANCE-FUTURES-DELIST-FORCED-CONVERGENCE-001 — PUBLIC SOURCE RECON LOWER BOUND
Date: 2026-10-05
Status: SOURCE RECONNAISSANCE ONLY — NOT SOURCE_GATE_PASS

## Purpose
Record a lower bound on mechanically qualifying USD-M perpetual settlement events found from official Binance public announcements before any market outcomes are opened.

## Mechanically qualifying examples already located
2024:
- FOOTBALLUSDT, BLUEBIRDUSDT — automatic settlement 2024-03-26
- ANTUSDT, DGBUSDT, CTKUSDT — automatic settlement 2024-04-01
- WAVESUSDT — automatic settlement 2024-06-11
- FRONTUSDT — automatic settlement 2024-08-23
- XEMUSDT, ORBSUSDT, LOOMUSDT — automatic settlement 2024-12-09
- MAVIAUSDT, OMGUSDT, BONDUSDT — announced automatic settlement 2024-12-16; OMG later postponed and must be adjudicated by final authoritative notice
- BLZUSDT — automatic settlement 2024-12-23

2025 examples:
- REEFUSDT — automatic settlement 2025-01-22
- EOSUSDT — automatic settlement 2025-05-21 as part of EOS -> Vaulta rebrand
- BSWUSDT — automatic settlement 2025-09-15
- UXLINKUSDT — automatic settlement 2025-09-26

This already establishes a lower bound comfortably above the frozen >=12 contract sample requirement, but it is NOT a complete census.

## Important source semantics
Announcements can be hidden inside broader spot-delisting or token migration/rebranding notices. Therefore title-only Futures searches are not sufficient for a complete census.

OMG also proves that settlement schedules can be amended/postponed. Final event authority must use the latest official pre-settlement notice and preserve the amendment chain rather than blindly using the first announced date.

## Market archive architecture
Binance's official public-data project documents public USD-M Futures archives and official downloaders for:
- klines/trades/aggTrades
- markPriceKlines
- indexPriceKlines
- premiumPriceKlines

The public archive also exposes a USD-M metrics family used for historical open-interest/ratio snapshots, but known archive gaps exist and must be treated as missing rather than imputed.

The pending source probe checks actual checksum-sidecar existence for a known qualifying event without opening market values.

## State
- sample-size lower bound: PASS
- exact forced-settlement mechanism: PASS
- complete reproducible 2024-2025 census: PENDING
- event-specific archive coverage: PENDING
- OI/metrics completeness: PENDING
- market outcomes opened: NO

No source-gate promotion is authorized until the pending items are resolved.
