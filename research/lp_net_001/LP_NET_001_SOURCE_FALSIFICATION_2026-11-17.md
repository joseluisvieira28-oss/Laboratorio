# LP-NET-001 — historical source-falsification and economic gate
Date: 2026-11-17. Research-only, no orders, live positions, paid data, wallet access, deployment, scheduled workflows, protected holdouts or merge. Child branch of PR #357.
## Question
Can a pool be selected **before** entry using information available then, so LP fees exceed impermanent loss, protocol fees, gas, swaps, risk and capital opportunity cost out of sample?

## First empirical attack: five complete public Uniswap v3 CSV files
Source repository: https://github.com/ThanosDrossos/IL_Measurement, pinned upstream commit `e75c0c566116b63a68107b9f8907071c53ca8ef2`; source data README describes one row per **burn**, not an independent completed position; historical data chiefly 2021–2024, not live 2026.
Read through authenticated GitHub connector and parsed directly as semicolon-delimited CSV, comma-decimal. The nine pools contain 30,058 **burn observations in publisher's full dataset**, but only the **five complete files below** were fully read; the four multi-megabyte full files were not materialized. Sample/first-100-position files must never be substituted as full independent data. **This is descriptive forensic analysis, NOT a forward backtest.**

| Exact file | Source blob SHA-1 | Burn rows | Distinct positions | Duplicate `id` keys | IL>+0.01 USD flags | Negative fee flags | Burn dates before 2022-05-01 | Net/initial sum 2021–22 | Net/initial sum 2023–24 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DAI_USDC_500 | ab68f0cf6690b57cd26e018a854b2c020947c934 | 414 | 370 | 12 | 48 | 2 | 38 | +0.498% | +0.222% |
| DAI_USDC_100 | a33090679d99868abc057564948fe4ad20557be7 | 816 | 720 | 23 | 84 | 0 | 11 | +0.369% | +0.029% |
| USDC_WETH_10000 | 80a36c21be612580b271f6817124a7affc3d0646 | 690 | 611 | 22 | 100 | 1 | 4 | −1.831% | −95.500% |
| USDC_WETH_100 | 5474fa89e3b9f75df238770bec286ff98a9ad067 | 473 | 416 | 22 | 52 | 0 | 0 | +0.052% | −17.439% |
| MKR_WETH_10000 | f057eac64330d955e80fafd98a2b5163dd646714 | 87 | 83 | 1 | 22 | 0 | 2 | +1.127% | −0.377% |

Metric is `sum(lossVersusHODLExact + event_feesUSD) / sum(initialValue)` within each historical period; **gross relative-to-HODL diagnostic only, not realized investable return**. Burn rows/positions are dependent, partly closed positions, with variable capital/duration, unclear gas and partial-collect attribution. No strategy holds equal capital for identical time intervals; this ratio is neither ROI nor APR nor per-position win rate. Real current protocol-fee splits can differ from historical fee attribution (https://developers.uniswap.org/docs/protocols/protocol-fee/concepts/fees).
One gross-era selection diagnostic: top among these five by 2021–22 naive return would be MKR/WETH 1% (+1.127%); its 2023–24 comparable reported figure is negative (−0.377%). This **does not constitute an OOS trial**, because pool universe/period/rule were chosen and analyzed retrospectively.

### Critical anomalies requiring chain-level reconciliation
- `USDC_WETH_10000`, event `517651#17627451`: `lossVersusHODLExact=-3,073,414,576.73`, `event_feesUSD=-14,870,356.18`, `initialValue=3,088,284,932.91` USD. It dominates pooled sums and is not an economic outcome to trust without raw event trace.
- Repeated `id=position_id#block` across several files; must inspect actual tx/log indices before considering rows distinct or accidental duplicates.
- Numerous `lossVersusHODLExact>0` flags (should not silently strip; ascertain subgraph valuation and partial-burn definitions); two negative fee cases in DAI_USDC_500 and one in USDC_WETH_10000; source rows dated before May 2022 contrary to reported observation window.
- Many real LP positions remain open; closed/burn-only selection introduces survivor/exit-selection bias. Counterfactual HODL and LP inventory must be marked at same timestamps and capital, with gas and custody accounted.
- **Do not clean away anomalous rows solely because they hurt measured profit.** Preserve immutable source bytes and report both sensitivity and objective ground-truth resolution.

### Falsification gate / decision
1. `RESEARCH_GO`: independent position-level onchain reconstruction, with immutable chain+block provenance, per mint/increase/decrease/collect, owner, token decimals, contemporaneous prices, fee tier, protocol fee schedule and paid gas.
2. Freeze pool and range universe, threshold/risk policy, max capital, dates and costs **before** future event outcomes. Compare positions to same-inventory HODL with same timestamps and to staying in cash; include gas+swaps+slippage+out-of-range time+depth+token depeg/contract risk.
3. Use chronological train/validation/untouched test and clustered uncertainty by pool/owner/day. Minimum actionable test requires positive incremental PnL after realistic execution frictions with conservative tail scenarios and prospective replication. Provisional fee-only history and past APYs are insufficient.
4. Until all are met, verdict **ECONOMIC_NO_GO / SOURCE-INTEGRITY BLOCKED**; not `NO_EDGE` for all LP strategies. No capital, no promises of income.
5. The parallel liquidity-shock hypothesis is unchanged: existing LIQUIDATION-PRESSURE-002-FORWARD source calibration ≠ PnL; LICP-001 forward NO_EDGE closed. Do not re-open LICP with cosmetic parameters.

## Reproduction
`replicate_source_gate.py` is a Python stdlib-only deterministic checker for the exact five pinned public CSVs. It expects these files locally under `--data-dir` with names `POOL_normalized_data.csv`. It verifies Git blob SHA-1 (Git object hash, not raw SHA-256), counts duplicate keys, positive IL, negative fees and dates; prints period diagnostics; emits JSON. It deliberately **cannot** promote an economic GO or access trading endpoints. Executed synthetic offline smoke test locally (pass); the five-source summary above was independently calculated from fetched GitHub file contents in this audit, not claimed to be a run of the script against mounted complete CSVs. To reproduce the entire dataset, acquire the five exact upstream files from the pinned commit; do not use changing main.
