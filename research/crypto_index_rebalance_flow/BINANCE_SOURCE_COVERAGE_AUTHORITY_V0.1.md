# CRYPTO-INDEX-REBALANCE-FLOW-001 — BINANCE HISTORICAL SOURCE COVERAGE AUTHORITY V0.1

Date: 2026-09-27
Status: FROZEN_SOURCE_ONLY / NO PRICE BYTES
Normalized-source run: 36329760208
Normalized-source artifact: 10935685669
Normalized-source artifact ZIP SHA256: 1614bf1520a1c56b8a9b7bab46a607aa3b56df05713fc0e14390f4dc8515ca80
Stable normalized event-set SHA256: fffaa5aab3ba17456358af230c3aeda10a74ba55078b6c98b3d1585916db5a17

## Technical amendment 001 — identity hash
The first coverage run (36329914764) stopped before any Binance HEAD request because the normalization `result_sha256` included `generated_at_utc` and was therefore intentionally non-reproducible across executions.

This is a technical identity bug only. No market bytes or outcomes were accessed.

The controlling identity is now the stable hash of the frozen normalized `events + ambiguous_source_records` payload:
`fffaa5aab3ba17456358af230c3aeda10a74ba55078b6c98b3d1585916db5a17`.

No event, ticker, direction, date, source exclusion, sample gate, market source, horizon or scientific rule changed.

## Purpose
Before opening any historical market outcome, prove that the exact official Binance Spot 1-minute archives required by the frozen 24-hour event geometry exist for a sufficiently large 2022-2024 corpus.

## Frozen market-data route
Official Binance public data only:
data.binance.vision/data/spot/daily/klines/{SYMBOL}/1m/{SYMBOL}-1m-{YYYY-MM-DD}.zip

For every required ZIP, the matching .CHECKSUM sidecar must also exist.

This gate performs HEAD requests only. It must not download or parse kline bytes.

## Exact symbol rule
Normalized Bitwise ticker -> exact Binance Spot symbol:
{TICKER}USDT

Control:
BTCUSDT

No aliases.
No quote-asset substitution.
No alternate exchange.
No current-listing proxy.
No nearest date.

## Required dates per event
For an official rebalance date D at the official 4:00pm ET boundary:
- UTC calendar day D-1
- UTC calendar day D
- UTC calendar day D+1

This is sufficient for exact T-24h/T0/T+24h boundaries because those times are 20:00 or 21:00 UTC depending on America/New_York DST.

An event leg is source-eligible only if the token and BTC each have ZIP + CHECKSUM on all three exact UTC dates.

## Holdout firewall
2025 event identities are already normalized source-only, but this gate MUST make zero Binance requests for 2025.

2026 remains under separate prospective authority.

## Advancement gates
SOURCE_COVERAGE_PASS requires, after mechanical source exclusions:
- >= 50 eligible unique 2022-2024 event legs;
- >= 20 distinct eligible rebalance dates;
- all 3 calendar years 2022, 2023, 2024 represented;
- >= 5 distinct eligible rebalance dates in each year;
- at least one ADD and one REMOVE;
- zero 2025 Binance requests;
- zero market-data response bodies read.

Failure is SOURCE_COVERAGE_INSUFFICIENT, not NO_EDGE.

## Forbidden
- GET of market archives;
- price parsing;
- returns;
- volume;
- PnL;
- outcome-dependent ticker mapping;
- data substitution;
- 2025/2026 market data.
