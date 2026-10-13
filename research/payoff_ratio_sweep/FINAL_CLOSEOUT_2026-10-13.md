# PAYOFF RATIO SWEEP 2R/3R/4R/5R — EXPLORATORY CLOSEOUT (2026-10-13)

**Decision:** HISTORICAL_DESCRIPTIVE_PASS / 4R BEST_OF_FIXED_PAYOFF_VARIANTS_IN_SAMPLE / ORIGINAL_PARENT_HIGHER_RETURN / NO_FORWARD_PROMOTION / NO_LIVE_GO.

## Reproducibility / source
- [Canonical workflow success #38356035850](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38356035850), commit `b18170e7537949c2e7d474b47d8b091b3ce8fc2e`.
- Official public BTCUSDT Binance USD-M hourly source + mark + funding 2020-02 through 2025-12; same 221 checksum-verified official source archives as 4R; no 2026 price outcomes accessed.
- [Artifact #11792728776](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38356035850), archive SHA256 digest `d0febeb421ba2c69bca551bcb7838ea42baae5724b870e484ae4875a7d0523af`; `full_diagnostic.json`, `HISTORICAL_SWEEP_REPORT.md`, `source_receipt.json`. All four ratios replayed against SAME verified source + costs.
- First test phase (original 4R tests and frozen ratio mathematics) **PASS**. Source gate **PASS**. Independent re-run exact known 4R BASE return `0.283296092471792` and STRESS `0.26323957585754676`, 111 closed / 30 winners in both, so 4R regression anchor **PASS**.
- Frozen comparison `research/payoff_ratio_sweep/EXPLORATORY_PROTOCOL_V0.1.md` created before exploratory run; original 4R engine and science protocol **unchanged**.
- This sweep is **POST-DISCOVERY HISTORICAL**; new relative target ranking is not OOS. Original Parent and 4R hypotheses were already chosen with prior knowledge of historical performance. NO trading accounts/private APIs/orders/spending/main mutation.

## Results (all return and DD values relative to initial account equity)

| Model | BASE closed n | BASE win n | BASE win % | BASE closed-equity return % | STRESS return % | BASE PF | BASE closed DD % | BASE MTM DD % |
| --- | ---:| ---:| ---:| ---:| ---:| ---:| ---:| ---:|
| PAYOFF 2R | 152 | 60 | 39.47 | +20.03 | +17.48 | 1.179 | −10.81 | −12.27 |
| PAYOFF 3R | 119 | 35 | 29.41 | +9.87 | +8.04 | 1.103 | −11.52 | −13.56 |
| **PAYOFF 4R** | **111** | **30** | **27.03** | **+28.33** | **+26.32** | **1.277** | **−10.06** | **−10.92** |
| PAYOFF 5R | 97 | 22 | 22.68 | +22.50 | +17.70 | 1.237 | −17.46 | −19.37 |
| BTC-CONVEX Parent 20% notional normalization | 89 | 21 | 23.60 | +32.46 | +30.59 | 1.447 | −10.79 | −14.06 |

STRESS 5R closes **98** trades (22 wins) because fee/slippage affects entry and chronological reentry. All models: one trade open at 2025-12-31 cutoff, **not counted as win or loss**. Its hypothetical close loss would be ~18–24 USDT, varying by model; no 2026 was fetched for its actual resolution.

### Observed realized payoff and actual empirical break-even (BASE)

| Model | Targets | Stops | Time exits | Avg realized winner on margin % | Avg realized loser on margin % | Historical observed break-even win % | Funding USD | Hours in market |
| --- | ---:| ---:| ---:| ---:| ---:| ---:| ---:| ---:|
| 2R | 60 | 92 | 0 | +19.29 | −10.42 | 35.06 | −918.62 | 25242 |
| 3R | 35 | 84 | 0 | +28.70 | −10.61 | 26.98 | −1037.36 | 27809 |
| 4R | 29 | 81 | 1 | +37.94 | −10.65 | 21.91 | −1222.75 | 29112 |
| 5R | 21 | 74 | 2 | +46.51 | −10.56 | 18.51 | −1381.54 | 31717 |

Wins/targets differ because time exits can be profitable. Stop and target are *synthetic bar-touch fills*, not live limit/stop fill guarantees; same-hour ambiguity is pessimistically stop first. Negative funding sums are net modeled funding cashflows for the portfolio, not verified MEXC funding receipts.

### BASE per-year closed-equity return (%)

| Model | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2R | +13.18 | +6.82 | −6.48 | +4.75 | +4.27 | **−2.81** |
| 3R | +1.06 | +8.99 | −8.39 | +8.87 | +6.18 | −5.81 |
| 4R | +6.04 | +11.60 | −6.63 | **+14.26** | +7.97 | −5.86 |
| 5R | +14.21 | +11.30 | **−14.55** | +10.69 | +7.21 | −4.97 |
| Parent | +5.16 | **+20.62** | −9.10 | +2.58 | **+19.70** | −6.45 |

## What was learned
1. **The intuitive monotonic 2R→5R improvement hypothesis fails.** 3R was worst on total return; 4R was best of fixed-target variations. Do not interpolate to an untested optimum.
2. 5R increased capital-in-market by ~2,605 hours vs 4R, produced fewer targets, larger drawdown and less return in BASE and STRESS. More distant targets can prolong risk and lose opportunity.
3. 2R raised win-rate to 39.47%, but average gains were smaller, yielding lower lifetime return than 4R. 2R had historically *least negative* 2025 (-2.81% vs 4R -5.86%); relevant for downside investigation, **not license for retroactive regime-switching**.
4. 4R (BASE ~+28.33% and MTM DD~-10.92%) underperformed Parent (+32.46%) in total return but had lower estimated MTM drawdown than Parent (~-14.06%). Parent's top three winners made 34.53% of gross positive PnL, versus 11.51% of 4R gross positive PnL. This is a historical risk tradeoff, not a confirmed economic edge.
5. 2022 and 2025 negative for all five models (2R/3R/4R/5R/Parent) — market regime/entry mechanism should be examined as *explanatory hypothesis* rather than tuning stop/target on these known years.
6. No variant's real-world profitability is proven: historical quote/BBO, mark/liquidation tiers, personal exchange fills/lot/tick and fee economics, independence and live survivability all remain unbound.

## Next economic task — **not another retrospective target sweep**
- Preserve 4R and Parent unchanged and start synchronized read-only forward shadow (following existing 2026-holdout governance).
- Measure real public quotes, spread, mark/liquidation visibility, fill-sensitivity, funding duration, and ordersize feasibility; reconcile exact execution venue before any micro-live claim.
- Study why 2022/2025 lost money. Any new entry/regime filter is a distinct pre-outcome hypothesis and cannot inherit in-sample success or use old closed outcomes as fresh OOS.
- Use economically scaled risk limits; 5R's worse drawdown demonstrates the danger of targeting the biggest bucket without considering holding time and frequency.

**No merge to main, no live trading, no exchange mutation.**
