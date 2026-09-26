# CROSS-VENUE-DIAMOND-REPLICATION-002 — OKX JAN/FEB-2025 SOURCE VALIDATION FREEZE — 2026-09-18

Status: FROZEN_AFTER_RAW_ACQUISITION_PASS_BEFORE_DECOMPRESSION
Candidate: CED1D-0031 — AVAXUSDT Momentum 20D CONTINUATION H1

## Frozen raw pilot receipts

RAW_PAYLOAD_ACQUISITION_PASS produced four provider ZIPs:
- AVAX-USDT-SWAP-candlesticks-2025-01.zip
  SHA256 3990132d74c9bfc34ab908974c934dd1ebe70e6fc51592d9c209c9aec4165803
- AVAX-USDT-SWAP-candlesticks-2025-02.zip
  SHA256 efb25ed5cb34a7059710fbd548af71524cde908dea04ffd295e417126a47a861
- AVAX-USDT-SWAP-fundingrates-2025-01.zip
  SHA256 35fc508327f5f3c7b9ea183818760ac88037dd51b1f13ced2ef1165c36b8b35a
- AVAX-USDT-SWAP-fundingrates-2025-02.zip
  SHA256 eeeae487ea582a7df2fa9a3b56af54a4e1112373dbde8d4312745b50659863cd

The provider returned both Jan and Feb packages for the Jan-01 to Feb-01 monthly request. This validation gate must resolve source-calendar semantics before full acquisition.

## Allowed decompression/parser scope

For the four byte-exact frozen ZIPs only:
- verify ZIP integrity and safe member names;
- enumerate member filenames;
- read CSV header names;
- identify timestamp column by header semantics;
- parse timestamp values only;
- record row count, unique timestamp count, duplicate count, min/max timestamp in UTC, and interval/gap distribution;
- for candlesticks, verify whether consecutive timestamps are exactly 60 seconds and report deviations;
- for funding, preserve actual event timestamps and report interval distribution only; do not assume an 8h interval.

Forbidden:
- persisting or calculating OHLC/volume values;
- persisting or calculating funding-rate values;
- signal/return/PnL/expectancy/PF/direction-performance calculation;
- opening any 2026+ source;
- changing strategy identity, costs or venue set.

## Pilot PASS rule

SOURCE_VALIDATION_PILOT_PASS requires:
- every downloaded ZIP hash matches the frozen hash above;
- all ZIPs pass integrity and path-safety checks;
- each expected ZIP contains parseable tabular data;
- timestamp column is unambiguous;
- timestamps are unique and monotonic after canonical sort;
- candle data has no unexplained minute discontinuity inside its observed source span;
- no timestamp reaches 2026.

A PASS authorizes only a separately frozen full 2024-09 through 2025 source acquisition/validation gate. It does not authorize outcomes.
