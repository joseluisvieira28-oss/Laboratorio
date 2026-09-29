# DLS — MARGINFI SOL MARCH 2024 EXACT-SLOT RATE-LIMIT HOTFIX V0.2.1

Date: 2026-09-29
Branch: dls-marginfi-transient-reversion-v01
Status: FROZEN OPERATIONAL HOTFIX / SOURCE-ONLY / NO MARKET OUTCOMES OPENED

Parent authority:
MARGINFI_SOL_FEBMAR_SOURCE_PREREQUISITE_ADDENDUM_V0.2.md

Observed operational blocker:
canonical March SOL-only source run 36589912203 failed at exact-slot transport because one slot
(252069267) exhausted retries with HTTP 429.

This is a transport-rate-limit failure only.

## Unchanged science

No changes to:
- March canonical field-enrichment population;
- SOL asset-bank selection;
- bank registry;
- Jupiter route-member rule;
- SwapEvent decoder;
- route-root semantics;
- ordered simple-chain semantics;
- direction semantics;
- source PASS thresholds;
- any market-return hypothesis.

## Transport-only change

For March 2024 only:
- reduce exact-slot worker concurrency from 24 to 4;
- increase exact-slot attempts from 9 to 15;
- use exponential backoff capped at 60 seconds for HTTP 429 / 5xx;
- preserve exact same slot request schema and exact same population.

No failed slot may be dropped.
Any permanently unresolved slot remains SOURCE_BLOCKED.

## Firewall

prices=false
returns=false
pnl=false
feb_mar_market_outcomes_opened=false
apr_jun_2024_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
