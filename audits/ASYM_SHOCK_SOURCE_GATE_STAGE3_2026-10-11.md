# SHOCK-BREAKOUT-ASYM-001 — STAGE 3 SOURCE/EXECUTION GATE
Date: 2026-10-11
Status: CONTRACT_META_RUN_PENDING / NO ECONOMIC VERDICT / RESEARCH ONLY
Branch: research/asymmetric-shock-breakout-2026-10-11
PR: https://github.com/joseluisvieira28-oss/Laboratorio/pull/188 (DRAFT)

## Already verified independent public evidence
- Public BBO single-snapshot source gate: run 38134977278, PASS_ONE_SNAPSHOT_ONLY BTC_USDT and SOL_USDT, 14 synthetic tests pass, artifact 11700617067.
- Continuous 75.383s public BBO observation: run 38135111448, 16/16 valid BTC and 16/16 valid SOL; 18 synthetic tests pass, SOURCE_CONTINUITY_PASS_BOUNDED, artifact 11700268522.
- Neither claim demonstrates tradable execution, shock-specific source quality, or any prospective economic win rate.

## New source gate submitted today
Commit cf4f54a71bdb9eab3e5bafcc9672435468bd534d adds:
- Official-public MEXC contract metadata GET /api/v1/contract/detail/country?symbol={symbol}.
- Exchange public clock GET /api/v1/contract/ping.
- Symbol, contractSize, minVol, volUnit, priceUnit, futureType, enabled/state,
  apiAllowed public indicator, feeRateMode, takerFeeRate.
- New nine synthetic tests and no-auth public BTC/SOL metadata receipt.
- Indicative minimum contract notional from public ask, NOT executable liquidity capacity.
- Explicit fee mismatch flag versus May28 MEXC Jun1 API-fee announcement
  0.08% taker PER SIDE. Public contract metadata is NOT allowed to reduce
  operator-specific execution cost assumptions automatically.

At audit writing, GitHub Actions run 38137116005 was PENDING with zero jobs.
The source gate is NOT yet passed; evaluate actual job and JSON artifact when
terminal, distinguishing COMPLETE/PASS from SOURCE_META_BLOCKED and CI error.

## Important source notes
BLS official calendar:
https://www.bls.gov/schedule/2026/10_sched_list.htm
Next CPI Sep 2026 release: 2026-10-14 08:30 US Eastern (12:30 UTC,
14:30 Europe/Zurich). Calendar is an OUTCOME-BLIND source boundary.
Do not infer direction from an official event timestamp; post-release
consensus provenance is still blocked in older News Shock V0.3.

Official MEXC Futures public contract fields:
https://www.mexc.com/api-docs/futures/market-endpoints/get-contract-info
MEXC fee announcement:
https://www.mexc.com/en-GB/announcements/article/updates-to-api-futures-trading-fees-jun-1-2026-17827791535742

## Next gate (not activated in this note)
- Inspect final JSON of public-contract metadata and reconcile API eligibility,
  minimum contract notional, tick/volume step, and fee contradictions.
- If only public source passes, create an *independent* source-only shock-time
  receipt protocol frozen BEFORE 2026-10-14T12:30:00Z. Any collector must
  record clock drift, missed slots, crossed/stale quotes, capture start/stop
  and immutable source data, and must fail-closed if it misses the causal
  pre-release boundary.
- A true asymmetric *trading* outcome study needs a separate one-primary
  pre-outcome freeze specifying side, causal detection lag, stop/TP fill
  rules, cost budget, exact market and economic gates; do NOT retroactively
  derive a profitable strategy from future source-only CPI receipts.
- Preserve original LICP forward SOL family and ETF Q4 2026 locks.
- NO external spending, paid market data, orders, accounts, wallet access,
  live trading, main merge, post-outcome tuning or CI-green=>EDGE promotion.

## Actual CI feedback / bounded repair

GitHub Actions run 38137116005 completed FAILURE before source fetch.
26/27 synthetic tests passed; 1 mismatch unit test rejected the
operational classifier: a mismatched source symbol produced
CONTRACT_SCHEMA_UNEXPECTED instead of CONTRACT_IDENTITY_FAIL.
This is a purely technical taxonomy defect, NOT an economic outcome
or source-availability result. No metadata receipt was generated.

Repair commit 7b643d2276d9c4800ad5eaf8079f5f757cafc68e:
a single contract metadata dictionary carrying a symbol is now accepted
for identity validation; mismatching symbol is rejected with the correct
CONTRACT_IDENTITY_FAIL; no scientific assumptions changed.
New GitHub Actions run 38137239747 admitted but PENDING at this audit;
do not claim tests passed or gate succeeded until completed and receipt
has been read.

SOURCE_GATE_STATE = AWAITING_CORRECTED_CI_AND_ACTUAL_PUBLIC_RECEIPT.
ECONOMIC_VERDICT = UNTESTED.
