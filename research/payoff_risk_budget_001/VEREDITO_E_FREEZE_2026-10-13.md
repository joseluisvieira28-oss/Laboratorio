# CRYPTO LAB — PAYOFF 4:1 / Auditoria de risco e freeze (13 Oct 2026)

**VEREDITO: RETROSPECTIVE_RISK_BUDGET_CALCULATED / PAYOFF_4_TO_1_NOT_YET_VALIDATED / NO_LIVE_GO.**

Research-only, no merge to main, no orders, capital, account or exchange mutation. Based on PR #193 (historical first-touch) and the published, already-open BTC-CONVEX causal replay. No 2026 sealed holdout opened.

## Sources checked

- [BTC causal replay](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/35911267608), artifact 10772639953, `CAUSAL_1H_REPLAY_V0.1.json`, local SHA256 `b03c2513a5787e4d5ceeedb149c3a722a83961443baa1dba0068298c8da403c3`.
- [Parent ETH/SOL/BNB all-cost model](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/35918769969), artifact 10775714534.
- [PAYOFF +40/−10 first-touch](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38269021214), artifact 11755773347, event JSON hash `20ee665123663dc8575f66cd50addee52a6fb46c7edbdfa2ed031191214ac804`.
- [Original freeze](https://github.com/joseluisvieira28-oss/Laboratorio/blob/research/payoff-first-touch-identifiability-2026-10-12/research/payoff_first_touch/RETRO_FIRST_TOUCH_FROZEN_PROTOCOL_V0.1.md).

## Best published BTC mechanism — not independent, not a new 4:1 strategy

Original 1h causal replay: 93 closed trades; 23 wins / 70 losses, 24.73% win rate; +274.12% fee-only equity return, PF 1.311, closed-equity DD −40.75%, **funding and slippage absent**. Removing its three largest money winners turns PnL negative (−20,111.79 USDT). The average historical winning **position return** is +22.3253% versus average losing −4.1960%, ratio 5.32:1; this is the original exit rule, **not** fixed 4R. The year 2025 was negative.

## Additional independent calculation of fixed risk-budget scenarios

Take exactly the **same 93 known causal entry/exit pairs**, do not regenerate signals, initial equity 10,000 USDT, exactly 10% of evolving equity as hypothetical isolated margin for each successive position, 2× notional/margin, one active trade, no added margin. Long price ratio `q = exit_fill/entry_fill`; cash PnL/margin `= 2[(1−f)*q − (1+f)]`, with entry_fill `= entry*(1+s)`, exit_fill `= exit*(1−s)`, f fee/side and s adverse slippage/side. Equity updated by `equity *= (1 + .1 * PnL/margin)`. **Funding is missing, and slippage is an assumed sensitivity, not observed.** Source exit prices are reused; this is neither new targets nor portfolio-level execution evidence.

| Scenario | Retorno hipotético da equity | Máx. DD equity fechada | Ganho/perda médios sobre margem | Fechos ≥ +40% margem |
|---|---:|---:|---:|---:|
| fee 0.08%/side, slip 0 | +50.11% | −10.01% | +44.74% / −8.31% | 10/93 |
| fee 0.08%/side, slip 2bp/side | +48.98% | −10.15% | +44.64% / −8.39% | 10/93 |
| fee 0.08%/side, slip 5bp/side | +47.30% | −10.36% | +44.50% / −8.50% | 10/93 |
| fee 0.10%/side, slip 2bp/side | +47.87% | −10.29% | +44.55% / −8.47% | 10/93 |
| fee 0.10%/side, slip 5bp/side | +46.20% | −10.50% | +44.41% / −8.58% | 10/93 |

The year **2025: −5.63%** in fee-only 0.08% scenario. One published trade has entry timestamp equal to exit timestamp; included unchanged, not silently repaired. 5/5 offline synthetic fee/target/slippage calculations passed before publication. **These hypothetical positive results are not all-cost net performance and award zero promotion credit.**

## PAYOFF 4:1 proper — 12 Oct 2026 veredito remains intact

Historical original hold-windows 2020–25: 18 first target touches, 0 first stop touches, 71 **right-censored** old exits. The original −4% price stop is *tighter* than the hypothetical −4.8438751% price stop. Therefore 18/89 cannot be used as new win rate; 71 are not automatically losses, and neither PF nor new-strategy PnL is identifiable. 7/89 proxy entry mismatches >1%, including one target-touch case. No fills, funding, mark-liquidation, spreads, portfolio accounting or independent validation.

## Prospectively specified candidate: PAYOFF-40-10-BTC-001

**This is a new exploratory mechanism specification informed by already-seen historical outcomes, NOT a passing test or an executable bot.** No historical 2020–2026 result above can promote it.

- **Signal:** only complete BTCUSDT USD-M UTC 1h candles; parent Quant Trailing v5 LONG entry using RSI Wilder14<30, zScore(close,20)<−2, close<SMA20−2×stdev20, volume>SMA20(volume), score≥3, regime close>SMA200(close). Entry at next completed-bar open; one slot; no same-bar reentry/pyramiding.
- **Size:** maximum 10% of current available equity as initial isolated margin, 2× leverage, no margin top-ups. Experience limit, not proof of account safety.
- **Nominal barriers from hypothetical 0.08%/side taker fees before all other costs:** target entry price ×1.20176140912730184; stop entry price ×0.95156124899919936. Plan +40/−10% *on initial margin*, but actual net after funding/slippage/gaps is NOT guaranteed 4:1.
- **Expiry:** time-exit at next available hourly open after 60 UTC days, if neither barrier was touched. This new choice was informed by already-seen durations and requires **only fresh forward observations**. If stop and target intrabar ordering unknown, classify `AMBIGUOUS` and count conservative stop-first for diagnostics; stops are not guaranteed fills.
- **Source safety:** avoid mixing Binance price events with supposed MEXC exact fills; bind correct execution venue, public BBO, funding cashflows, mark-liquidation, costs, lot/tick rules, and causal source timestamps. Missing economic component ⇒ `ALL_COSTS_UNPROVEN`, no trade promotion.
- **Evaluation boundary:** earliest fresh observation after **2026-10-14 00:00 UTC** and freeze commit, if not conflicting with a separately frozen 2026 holdout. Existing previously-seen 2020–2026 results stay `DIAGNOSTIC_ONLY`. No retuning after first new signal/outcome.
- **Gate:** require an independently specified power/forward sample, uncensored trades including time exits, daily-cluster uncertainty, positive net BASE/STRESS expectancy and PF, exposure/drawdown constraints and venue feasibility. This file does **not** claim these gates passed.

## What was actually completed, vs not

**Done:** independently re-read source artifacts, reproduced the historical tail-dependence, computed a risk-budget ledger with five sensitivity scenarios, froze a candidate hypothesis before future samples.

**Not done / not falsely claimed:** no new 4:1 full-history portfolio backtest, no proof of full costs, no forward sample, no production trading bot, no trade/exchange request, no main merge or micro-live GO.

Next valid development stage is an *offline no-lookahead implementation and synthetic QA* of the above fixed entry+target+stop+time-exit logic and fresh read-only prospective capture. Any new data used for discovery cannot also be relabeled independent OOS.
