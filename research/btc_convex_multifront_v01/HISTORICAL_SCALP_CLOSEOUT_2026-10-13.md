# BTC-CONVEX FAST REBOUND SCALP — RETROSPECTIVE ECONOMIC VERDICT
**Date:** 2026-10-13 UTC
**Experiment:** FAST-REBOUND-SCALP-001 exploratory historical diagnostic under a distinct frozen protocol.
**Authority:** `HISTORICAL_DIAGNOSTIC_PROTOCOL_2026-10-13.md` commit `060c26591c415107ca1cb7d7e0c2e07e30eb7ca1` **before** economic outcomes.
**Status: HISTORICAL_SCALP_FAIL / NO FORWARD RESOURCE PRIORITY / NO LIVE GO.**
No selection or retuning after outcomes.

## Verification
- Authoritative GitHub Actions: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38421864088 — SUCCESS
- Artifact: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38421864088/artifacts/11826863803 (ledger CSV for 4 arms, historical result JSON including official source SHA256 manifests)
- Job log: 20/20 offline regression tests PASS (15 prior engine + 5 historical). Source/data+replay success.
- Archived market: 2021-01..2025-12 UTC full contiguous Binance USD-M BTCUSDT **525,888 5m bars**, **44,568 1h bars including December 2020 warmup**, **5,478 public funding records**, 60 consecutive fully checked economic months, 181 signed monthly ZIPs (each matched the publisher CHECKSUM; 1 warmup + 60 x 3 market/funding).
- Original recovered Quant Trailing V5 RSI/SMA/zscore signal code imported from the preserved Parent branch; first 5m entry strictly after completed 1h signal witness, one slot, max 4h. Fee 8bps per side, BASE 2bps slip side, STRESS 5bps slip side; historical funding rate with 5m market-price *proxy* for funding mark; 20% initial paper equity notional 1x, initial 10,000 USDT. This is modeled Binance historical, not MEXC fill/quote or account proof.

## Exact historical models 2021–2025, all five annual PnL intervals loss-making
| Arm | Closed trades | Wins | Win% | Final paper equity USDT | Return | PF | Closed equity DD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Scalp BASE | 588 | 172 | 29.2517 | 7,781.1351 | **-22.18865%** | **0.40560** | -22.18865% |
| Scalp STRESS | 592 | 158 | 26.6892 | 7,286.5738 | **-27.13426%** | **0.31879** | -27.13426% |
| Delay-6h control BASE | 511 | 146 | 28.5714 | 8,021.1007 | -19.78899% | 0.394998 | -19.88079% |
| Delay-6h control STRESS | 518 | 133 | 25.6757 | 7,528.4995 | -24.71500% | 0.30597 | -24.71500% |

SCALP BASE exit reasons: 388 STOP_FIRST, 140 TARGET, 60 TIME_EXIT, 0 recorded gaps; 47 repeated signals skipped due active slot. 635 hourly Parent signal bars do NOT mean 635 independent events.
SCALP BASE fees 1,663.6261 USDT, funding -9.9230; return in money -2,218.8649 USDT.
Price PnL on unchanged simulated trades including adverse slippage but **before fees/funding** arithmetically = -2,218.8649 + 1,663.6261 + 9.9230 = **-545.3158 USDT**. Thus simply deducting zero fees from this fixed ledger does not create an apparent gross positive result; not a full zero-fee portfolio replay with recomputed size/trades.
Scalp STRESS fees 1,625.9755; funding -9.4210, also negative before accounting for fees.

Annual SCALP BASE PnL in USD: 2021 -598.716; 2022 -450.347; 2023 -269.078; 2024 -586.798; 2025 -313.926. ALL NEGATIVE. Delay-6h placebo losses do not prove paired statistical superiority or noninferiority because entry overlap and trade counts differ.

## Scientific interpretation
The frozen 4-hour price +0.75% / -0.35% quick-rebound hypothesis **does not exhibit positive after modeled cost historical economics** even though the Parent mechanism can capture multi-day right-tail trends. Idealized two-barrier break-even win rate after modeled 8bps taker + 2bps slip is 48.1967%, whereas realized win-rate including TIME_EXIT was 29.25% (not directly interchangeable without incorporating timeout distribution). Mechanical reason is lower target capture vs frequent stops/time exits and costs.
No extra cost model tuning or target/stop sweep may rescue this identifier using the already-seen 2021–25 outcomes. Its predeclared future gate should be marked **NOT ACTIVATED / LOW PRIORITY**, without altering the original Parent or rewriting the previously frozen future protocol.

## Limitations
Historical candles already exposed to this research family; NOT independent OOS. 5m high/low sequence still unknown inside bars; conservative stop-first was applied. Market-price proxy fills at a fixed 5m open are not bid/ask/depth, funding price is not exchange settlement mark, no MEXC actual fee tier, min lot, market impact, account liquidation, latency or real rejected orders. This study does NOT prove BTC-CONVEX Parent unprofitable or rule out a truly different economic quick-rebound hypothesis. 20/20 tests prove implementation invariants, not the actual fill feasibility.

## Verdict and next economic allocation
**Stop further execution/forward investment in this exact F2 scalp child.** Preserve Parent 1h trailing and independent F1 quote-observation execution study separately; only resume if a genuinely economically distinct, preregistered causal hypothesis (not retuned stop/target on the same data) is introduced. Original protected 2026 holdout untouched, main unchanged; zero orders, no private account, spend, Render, trading or wallets.
