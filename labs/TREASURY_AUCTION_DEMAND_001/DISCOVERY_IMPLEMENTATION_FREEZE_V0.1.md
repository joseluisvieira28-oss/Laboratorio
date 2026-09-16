# TREASURY-AUCTION-DEMAND-001 — DISCOVERY IMPLEMENTATION FREEZE V0.1

Date: 2026-09-16

Status: `IMPLEMENTATION_FROZEN / BTC_OUTCOMES_NOT_YET_OPENED`

- MVE: `TAD-BTC-D1-001`
- Pre-Discovery authority commit: `7ca8527df76340222cf678f9538ae79e711c6845`
- Frozen runner commit: `7efe544c6d398ff118c256b6a8513f0d5d64a489`
- Runner: `labs/TREASURY_AUCTION_DEMAND_001/discovery_v01.py`
- Frozen Treasury canonical SHA-256: `ab2695123b04c6e320bda23e5496b1dcfadabec8c6784211a10407ac87499892`
- Discovery BTC period: 2021-01-01 through 2023-12-31 only.
- BTC 2024 outcome access: forbidden by this runner.
- BTC 2025 outcome access: forbidden by this runner.
- BTC 2026 outcome access: forbidden by this runner.
- BTC source: Binance Spot BTCUSDT official Data Vision monthly 1d archives only.
- Every Binance ZIP must equal the provider `.CHECKSUM` SHA-256.
- Signal, same-date conflict handling, D+1 entry, 1-day hold, NET10/NET20 costs, bootstrap and all promotion gates are exactly those in `PRE_DISCOVERY_AUTHORITY_V0.1.md`.

Any scientific-rule modification after the first BTC outcome access is prohibited. A purely technical failure may only receive a minimal technical repair that does not alter the frozen scientific contract; such a repair must be documented before rerun.
