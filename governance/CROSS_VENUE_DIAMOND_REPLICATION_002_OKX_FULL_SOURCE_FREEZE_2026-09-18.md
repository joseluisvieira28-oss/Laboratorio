# CROSS-VENUE-DIAMOND-REPLICATION-002 — OKX FULL SOURCE ACQUISITION & VALIDATION FREEZE — 2026-09-18

Status: FROZEN_AFTER_SOURCE_VALIDATION_PILOT_PASS_BEFORE_FULL_HISTORICAL_SOURCE_ACCESS
Candidate: CED1D-0031 — AVAXUSDT Momentum 20D CONTINUATION H1
Venue: OKX AVAX-USDT-SWAP

## Pilot facts preserved

The Jan/Feb-2025 source-validation pilot passed:
- byte-exact pilot hashes matched;
- candle timestamps unique, gap-free at 60 seconds;
- funding timestamps unique, observed 8-hour spacing in the pilot;
- OKX monthly module-2/module-3 archives are aligned to UTC+8 month boundaries:
  - 2025-01 candle file: 2024-12-31T16:00:00Z through 2025-01-31T15:59:00Z;
  - 2025-02 candle file: 2025-01-31T16:00:00Z through 2025-02-28T15:59:00Z.

No OHLC or funding-rate values were persisted or used.

## Frozen full source set

CANDLE MODULE 2:
- exact required monthly files: 2024-09 through 2025-12 inclusive;
- purpose: frozen warmup plus full 2025 replication source;
- API requests, respecting current <=10-month range:
  1. begin 2024-09-01, end 2025-06-01, monthly, instFamilyList=AVAX-USDT;
  2. begin 2025-07-01, end 2025-12-01, monthly, instFamilyList=AVAX-USDT.

FUNDING MODULE 3:
- exact required monthly files: 2025-01 through 2025-12 inclusive;
- API requests:
  1. begin 2025-01-01, end 2025-10-01;
  2. begin 2025-11-01, end 2025-12-01.

All requests:
- endpoint /api/v5/public/market-data-history
- instType=SWAP
- dateAggrType=monthly
- instFamilyList=AVAX-USDT.

## Validation

For every required provider ZIP:
- follow only provider-returned HTTPS groupDetails URLs;
- preserve original bytes and SHA256;
- ZIP integrity/path safety PASS;
- enumerate CSV header;
- parse timestamp column only;
- zero duplicate timestamps;
- candle files: every consecutive timestamp within each file must be exactly 60 seconds;
- all required month filenames must be present exactly once after hash-consistent deduplication;
- global candle timestamp union must have no discontinuity across adjacent files;
- global funding timestamp union must be strictly ordered and duplicate-free; interval distribution report-only;
- no timestamp >= 2026-01-01T00:00:00Z may be opened or persisted.

## Outcome lock

No OHLC/volume/funding-rate values may be persisted or used.
No signal, returns, PnL, expectancy, PF or direction-performance calculations.
No tuning, venue dropping, live trading, orders, authenticated exchange mutation, wallets, alerts/webhooks, or main merge.

PASS classification: OKX_FULL_SOURCE_DATA_PASS.
A PASS authorizes a separately frozen Stage-B exact replication implementation, not live trading.
