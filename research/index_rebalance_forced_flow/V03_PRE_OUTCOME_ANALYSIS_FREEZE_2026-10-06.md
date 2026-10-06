# INDEX REBALANCE V0.3 — PRE-OUTCOME ANALYSIS FREEZE
Date: 2026-10-06. FROZEN BEFORE MARKET OUTCOMES.
Family: CRYPTO-INDEX-REBALANCE-FORCED-FLOW-001
Comparable subfamily: COINDESK20-REBALANCE-FORCED-FLOW-001
Source authority commit: ec519e9c7f06e6de78639b3fb8c6d3b671f1a84a.
Parent V0.2 remains preserved, never silently rewritten.

## Changes before first outcome
The operator requires costs/slippage to be frozen before discovery. Legacy V0.2 omitted costs and did not activate. V0.3 therefore preserves all nine gross gates and adds two cost-model gates BEFORE first outcomes. July source date is corrected to June 20, as documented source conflict, independent of prices.
No historical market outcome has been opened in this mission; only metadata/checksum source coverage and synthetic code checks.
The old V0.2 runner is not activated or run as a parallel competing experiment.

## Universe and direction
All 14 source observations in source adjudication, including CRO even though its Binance pair lacks source coverage. No venue shopping.
ADD: +1 token leg and -1 BTC benchmark leg.
DELETE: -1 token leg and +1 BTC benchmark leg.
Fixed initial equal USD notional, normalized per token-leg notional (gross two-leg exposure is 2x this denominator). BTC-relative metric is not total-capital ROI.
Only ADD/DELETE. Retained constituents' weight changes have no valid trade direction absent drift-adjusted old holdings; excluded from this hypothesis BEFORE prices.

## Knowledge and primary horizon
Calendar provenance only. Not exact first-publication time.
Conservative public date=max official PDF and archive dates if different.
Entry=open of 1m bar at 00:00 UTC TWO calendar days after conservative public date.
July 2024 entry=2024-06-22T00:00Z.
Effective=16:00 America/New_York on official implementation date; correct DST.
Exit=close of last complete 1m bar ending at/before effective minus 5 minutes; bar opens at effective minus 6 minutes.
Only 2024–2025. All 2026 market values CLOSED.

## Source/transport
Binance public spot daily 1m klines, USDT pair and BTCUSDT. Check SHA256 against official .CHECKSUM before parsing. Four maximum concurrent public archive reads, three identical transport attempts, no alternate venue/filename inference.
Exact timestamp and positive finite OHLC required; duplicate bars, invalid geometry, checksum failure -> SOURCE_INCOMPLETE.
At least 12/14 complete observations required BEFORE outcomes are calculated. Missing CRO is source exclusion, not zero return.
No sample exclusion based on a return.
If <12 -> SOURCE_BLOCKED, no summary economic gate evaluation.
Only endpoint-day archives read. No secondary horizons, full paths, MFE/MAE, or 2026.

## Outcomes/control/clusters
R_asset=exit/entry-1; R_btc=BTC_exit/BTC_entry-1.
SIGNED_RAW=direction*R_asset.
SIGNED_EXBTC=direction*(R_asset-R_btc).
BTC same-time return is a benchmark/control, NOT a matched non-event causal control.
Each quarter is one shared-information cluster; 14 asset observations across five changed-quarter clusters. Zero-change quarters retained in source census, not fabricated trade events.
Report leave-one-observation-out and leave-one-quarter-out. No naive independence/significance claim.

## Frozen cost/slippage model
Model assumptions, NOT observed historical fees, quotes or borrow availability:
Per transaction per leg: fee 10 bps + slippage 10 bps.
Four transactions for two-leg round trip => fixed 80 bps per token-leg notional.
One short leg always exists; carry/borrow stress allowance=10 bps per elapsed day, prorated actual seconds from entry to exit close.
C=0.008+0.001*holding_days.
NET_MODEL=SIGNED_EXBTC-C.
No leverage, no actual borrowing, no fills. Unknown borrow availability/capacity is unresolved; SURVIVES_DISCOVERY could only authorize later execution feasibility, never trading. Fixed cost model is a screening assumption, not proof of executable PnL.

## Gates — ALL eleven required
Preserve nine original gross gates:
1. n>=12.
2. median SIGNED_EXBTC>1%.
3. positive SIGNED_EXBTC hit rate>=65%.
4. median SIGNED_RAW>0.
5. every observation LOO median SIGNED_EXBTC>0.
6. every changed-quarter LOO median SIGNED_EXBTC>0.
7. max positive single-observation contribution / sum positive SIGNED_EXBTC<=35%.
8. median ADD signed excess>0.
9. median DELETE signed excess>0.
Cost-model gates:
10. median NET_MODEL>0.
11. every changed-quarter LOO median NET_MODEL>0.

Taxonomy:
SOURCE_BLOCKED: inadequate verified market endpoints (<12); hypothesis not tested legitimately.
NO_EDGE_DISCOVERY: verified source >=12, any of eleven gates fails.
SURVIVES_DISCOVERY: all eleven pass; association survives this model, execution unproven.
Bitwise remains separately SOURCE_BLOCKED_HISTORICAL / FORWARD-ONLY.

## Once-only activation
A separate activation receipt must exist. Workflow activates by the unique receipt path on this isolated branch only. No schedules, no pull request events, no main writes. Receipt addition is the only trigger; evidence directory refuses overwrite in a workspace. Check Actions history before relaunching: if a legitimate result exists, do not run again.
Transport failure before legitimate outcomes may only be repaired with preserved rules.
After any valid result: do not change dates, direction, costs, benchmark, exclusions, horizons or thresholds to rescue it.
No secondary metric can reverse primary failure.
Research only; all operator prohibitions remain.
