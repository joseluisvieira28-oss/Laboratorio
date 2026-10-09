# BTC-CONVEX-TREND-CAPTURE-001 — V0.2 Independent Refresh / Read-Only Verdict
Date: 2026-10-09
Mode: RESEARCH-ONLY; NO TRADES, NO CAPITAL, NO MAIN MERGE.
Status: `FORWARD_INSUFFICIENT`; strict `NO_LIVE_GO`.

## Authority and frozen science
Original authority: `labs/btc-convex-trend-capture-001/PROSPECTIVE_SHADOW_AUTHORITY_V0.2_AGGRESSIVE.md` on `btc-convex-trend-capture-001-v0.1`, freeze SHA 673d50b2f786e88c593a900db1a9aac6a265d215.
Frozen 1h Parent V5 long-only, BTCUSDT/ETHUSDT/SOLUSDT/BNBUSDT; 95% of separate 10,000 USDT per-symbol hypothetical accounts; 4% hard stop, recovered trailing logic unchanged, 10 bps per side fee, 2 bps adverse slippage per side and official historical futures funding. First eligible 1h bar open 2026-09-24 07:00Z. Existing V0.2 sample checkpoints: A >=10 resolved; B >=25 and >=2 symbols >=5; C >=50 and >=3/4 symbols >=5 plus source/causal integrity and V3 board. No automatic promotion.

## New evidence (read-only, 2026-10-09)
Independent isolated branch `ops/btc-convex-v02-readonly-verdict-2026-10-09`.
Workflow run `37885894369`: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37885894369
Workflow commit `3ae90359e590252e990ab1c3bee679a63d224e2d`.
Result: completed SUCCESS, original frozen snapshot runner success, original validator success, independent internal causal/replay rule checks success; no science changes.
Artifact ID `11596258168` (`btc-convex-v02-readonly-verdict-2026-10-09`).
Snapshot UTC: `2026-10-09T04:52:27.912671+00:00`.
Snapshot JSON SHA256: `98b206cdf3efaa8f46e972faec3c5b891cbbc8d08b4d70fa2168d2c99b61a8b1`.
Independent forensic JSON SHA256: `c909c4f92ae3674df760943dc475e5a83410380760cc46c6fbde80c914522604`.

All four source nodes PASS in this snapshot; frozen replay reports 3 closed, zero symbol with >=5 closed, 1 BTC open, 0 open ETH/SOL/BNB.
| Symbol | Resolved | Open | Hypothetical separate-account marked return |
| --- | ---: | ---: | ---: |
| BTCUSDT | 0 | 1 | -1.180686851% |
| ETHUSDT | 1 | 0 | -4.172102361% |
| SOLUSDT | 1 | 0 | -4.100840465% |
| BNBUSDT | 1 | 0 | -4.011152862% |
Family mean of separate-account marked returns: -3.366195635%. It includes one open BTC position, and is NOT a deployable portfolio return.
Resolved loss PnLs from hypothetical USDT 10k separate accounts: ETH -417.21, SOL -410.08, BNB -401.12 USDT. All three closed outcomes are losses.
V0.2 Checkpoint A 3/10 NOT REACHED; B 3/25 NOT REACHED; C 3/50 NOT REACHED. No evidence permitting promotion.

Comparison with previous artifact:
- Prior artifact from workflow 36523792686 / artifact 11518750694, snapshot `2026-10-07T23:31:25.776571+00:00`, JSON SHA256 `41e8410b01ccf93c1c2d5f8ff1a42a8a8fe7b8a4d2a5e8a00c0bd85614314942`.
- An independent local read-only comparison found unchanged prefix of all prior signal and resolved-trade records for all four symbols; no rewinding of bar counts and no internal next-hour entry/overlapping-position inconsistency. This is an *internal replay consistency* test, not full point-in-time or executable fills evidence.
- Prior snapshot contained 1 resolved ETH loss; Oct9 snapshot contains two further resolved SOL/BNB losses. No historic loss was edited.

## Critical integrity/feasibility limitations
1. Original `prospective_shadow_snapshot_v0_2_aggressive.py` **re-downloads and replays public historical 1h Binance OHLCV and funding data at each invocation**. Its `causal_integrity_blocker` field is currently hardcoded `False`. It is NOT independent evidence of a durable, append-only, observation-at-T0 ledger. Existing older snapshots help compare prefixes but do not prove every entry quote was available at a recorded decision time.
2. Model assumes fill at exactly next hourly open with fixed slippage. No contemporaneous order-book bid/ask, depth, quote-age, or exchange-order receipt supports executable fill at that instant. Classify as `EXECUTION_FEASIBILITY_UNVERIFIED`, not causal corruption proven and not real net profit proof.
3. Highly exposed: 95% of each separate simulated 10,000-USDT account allocated; typical price stop 4% => ~3.8% account loss before fees/gaps. Observed three losses ~4% each. This is not a small-capital low-risk cashflow solution.
4. Historical independent positive ETH/SOL/BNB replication remains scope-limited and contradicted by negative XRP/DOGE/ADA/LINK/AVAX cross-sectional expansion. Historical parent MTM drawdowns ~54-59% remain a material warning.
5. Three losses out of three are adverse descriptive evidence, not statistically sufficient proof of `NO_EDGE` or a reason to change the pre-frozen Parent.

## Adjudication
**Live GO: NO.**
**Independent executable NET edge: NOT DEMONSTRATED.**
**Exact V0.2 economic sample: FORWARD_INSUFFICIENT (3/50, 0/4 assets >=5).**
**Source/replay deterministic gate: PASS** only for this snapshot; `point_in_time_signal_provenance=NOT_DEMONSTRATED` and `actual_bid_ask_execution=NOT_DEMONSTRATED`.
Do not count GitHub workflow SUCCESS as profitability or authority. Do not promote/reselect from the results of failing samples.

## Legitimate next action
Continue immutable V0.2 research under the original frozen authority, without any retuning. For each new artifact verify timestamp/frozen symbols, prior-prefix immutability, missing bars, stop and trail path, funding/cost accrual, real-time source timeliness, and independently archive its hash before reading later outcomes. Alert at 10/25/50 original checkpoints; cannot force trade count, fabricate signals, or use a new closed historic period as untouched confirmation.
Separately, if true *executable* edge is the target, design and freeze a NEW live-observable quote/cost shadow experiment BEFORE its first eligible future observation. Preserve the existing V0.2 as descriptive replay and never reinterpret its older price-open fills as actual broker fills.
No real orders, private APIs, wallet/account access, funded deployment, or main mutation performed.
