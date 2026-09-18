# AAVE-CREDIT-STRESS-001 — SQD SOURCE GATE V0.2 CLOSEOUT

Date: 2026-09-18
Source gate: AAVE-CS001-SOURCE-002-SQD
Canonical run: 35315587454
Canonical head: 18002914fecf56f10e5ccf3140bc6fd2fe12f375

## FINAL CLASSIFICATION

SOURCE_DATA_PASS

## RECOVERY

The frozen V0.1 scientific source contract was preserved: Aave V3 Ethereum Pool, USDC reserve, ReserveDataUpdated topic, four exact 501-block 2024 windows, structural fields, and Binance 2023-2024 archive presence. Only transport changed from failed keyless JSON-RPC endpoints to the public SQD Ethereum-mainnet Portal, a transport already canonically validated by AAVE-LIQUIDATION-OVERHANG-001 across the enclosing historical Aave V3 block range.

## CANONICAL RESULT

- Q1 blocks 19000000..19000500: 16 matching USDC ReserveDataUpdated logs
- Q2 blocks 19650000..19650500: 73
- Q3 blocks 20300000..20300500: 19
- Q4 blocks 20950000..20950500: 9
- valid quarter probes: 4/4
- every window reached its exact frozen terminal block
- sampled logs contained transaction hash, log index, >=2 topics and data
- Binance archive presence probes: 4/4 PASS
- 2025 accessed: false
- 2026 accessed: false
- economic rate values decoded: false
- BTC market values/returns/PnL: unopened

## RELEASE

This PASS resolves the prior source-transport blocker. It authorizes the separately governed decoding/daily-series preparation and, only after a clean pre-outcome freeze plus explicit user authorization, the already-defined 2023-2024 Discovery mechanism. It does not itself establish an edge.
