# BTC-CONVEX V5 — RESIZE WITHOUT CURTAILING OUTLIER WINNERS — EX-POST HISTORICAL FREEZE V0.1
Date: 2026-10-09.
Operator mission: Determine whether substantially smaller **account-level position risk** retains favorable realized historical expectancy and asymmetric winners in archived BTC Convex 2021–25 trade ledgers, without modifying entries, prices, stops or trailing.
First frozen **before this child-experiment rescaling is computed**, BUT the source 2021–2025 market/trade outcomes ARE ALREADY KNOWN. There is no pristine 2021–2025 holdout remaining in this dataset; results are strictly exploratory diagnostic of fixed sizing, NOT independent OOS or a scientific rescue of failed cross-section.

## Exact trusted sources, scope
Three immutable earlier original per-asset trade-ledger artifacts, 2021-01-01 through 2025-12-31:
- first untampered ETHUSDT/SOLUSDT/BNBUSDT Parent V5, workflow 35918769969, artifact 10775714534, archive JSON CROSS_ASSET_COST_VALIDATION_V0.1.json; 3/3 historically profitable.
- adverse expansion XRPUSDT/DOGEUSDT/ADAUSDT/LINKUSDT/AVAXUSDT Parent V5, workflow 35921780080 artifact 10778258822; historically 0/5 profitable, must remain in aggregate.
- third LTCUSDT/BCHUSDT/TRXUSDT/DOTUSDT/UNIUSDT Parent V5 from workflow 35956632021 artifact 10791006099. H2 child must never be pooled with Parent (not tested here).
Use both unchanged original BASE (10bps fee each side; 2bps slippage each side; actual historic funding in ledger) and STRESS (10bps fee each side; 5bps slippage each side; same funding). No private endpoints, no new market data fetch. The original 95%-equity Parent capital allocation used trade notional = 0.95*prior_equity/(1+entryFee=0.001); original 4% underlying price stop before gaps, fees, funding. This freeze tests position sizing only.

## Fixed new position-sizing arms
Use existing original 4% **price** initial stop, trail trigger+5%, 12% trail, signals, entry/exit timestamps/prices/funding, no skip or threshold retuning.
- compare Original `95% allocation` (reference benchmark; not a risk recommendation) vs fixed nominal risk budgets `0.25%, 0.50%, 1.00%` of current sleeve-equity per trade, calculated as `notional_fraction = nominal_risk_budget / 0.04`, i.e. `6.25%, 12.5%, 25%` allocated to contract notional (not leverage).
- The 0.25/0.50/1.00% budgets target an **unfilled 4% price-stop move only**; actual realized equity loss may exceed them after costs, gaps and funding. Account stop loss is NOT guaranteed by this model.
- Each asset begins an **independent 10,000 USDT research sleeve**, no portfolio risk netting or shared-wallet claims. Per-symbol fixed-fraction compounding with preserved realized per-notional trade result `r_i=net_pnl_i/(qty_i * original_entry_price_i)` including fees+funding. For nominal budget `b` use next sleeve equity = prior_equity * (1+(b/0.04)*r_i); for 95%-benchmark use (0.95/(1+0.001)) * r_i. All original per-trade economics scale linearly in order size **by assumption**, no venue min notional, market impact, book depth, execution priority or changed funding tier. Mark this assumption CRITICAL. Stop/fill geometry unchanged, original 95% path should reproduce frozen ending equity within numerical tolerance before any child result is accepted.
- Detect negative/NaN equity and missing/inconsistent ledgers as SOURCE/COMPUTATION_BLOCKED, not zero/NO_EDGE.
- Preserve chronological trade IDs/times; consecutive non-overlap; positions are assumed same trade set; original bar-level MTM DD cannot be claimed for new sizing arms. Compute realized **closed-trade equity drawdown** ONLY and clear mark `INTRATRADE_DRAWDOWN_NOT_RECONSTRUCTED`; report benchmark closed-trade vs original MTM distinct.
- Compute total net return, CAGR over 5 calendar years (not trade frequency-adjusted), BASE+STRESS, closed-trade DD, # losing and winning trades, gross absolute-average-winner/loser ratio at each fixed size, historical annual returns from exit dates, worst realized trade account loss (%), maximal losing streak, PF in USDT, fees/funding already included in r_i.
- For each arm compute **MISSED_WINNER_TOP3**: identify top-three winning trades by per-trade percentage return `r_i` *before* rescaling, then replace their realized economic return by 0 at original timestamps, recompute the capital path. **This assumes missed/unfilled trades without alternative entries and is an ex-post stress diagnostic, not a historical counterfactual simulation.** No optimized subset.
- Additional adverse cost stress per traded notional: subtract **10 bps** per completed roundtrip from the **original STRESS** r_i before rescaling, to approximate added friction not observed. This is a hypothetical sensitivity, not a historical fee receipt.
- Do NOT select a single variant as "scientifically discovered" because all original data are opened. Present the 0.25%, 0.50%, 1.0% arms side by side with no profit-driven threshold optimization.

## Fixed post-computation classifications
- `RISKSCALE_MATHEMATICALLY_REDUCES_EXPOSURE` if (all three budgets produce finite, valid arithmetic with exact replay of original 95%-allocation benchmark); risks in price terms inherently smaller, but historical per-trade outcomes may still show nontrivial gap losses.
- `SCOPE_LIMITED_HISTORICAL_POSITIVE` for an arm only if all ETH/SOL/BNB 2021–2025 BASE & STRESS equity ending balances > start; this is an ex-post diagnostic, no independent OOS. Separately record `ALL_13_ASSETS_PASS/FAIL` with fixed 13-asset Parent universe; negative expansion cannot be deleted to rescue the family.
- `TAIL_DEPENDENCE_FAIL` if the best-3-missed scenario loses money in **>=2/3** of ETH/SOL/BNB even if baseline profitable; if not, `TAIL_DEPENDENCE_SURVIVES_DIAGNOSTIC`. This is a fragility diagnostic, not a hard universal statistical gate.
- `COST_STRESS_FAIL` if additional +10bps cost flips >=2/3 BASE-positive ETH/SOL/BNB sleeves to negative or worsens generalization.
- If smaller risks preserve only tiny returns, label `LOW_CAPITAL_RETURN`; report annualized percent and no arbitrary income target. No fixed required CAGR threshold.
- Real-money/historical-independent edge is NEVER inferred solely from ledger rescaling. No live GO or trading authority.

## Caveats / protected actions
- Ex-post: The arm choices are specified before this computation but after original historical outcomes were inspected. It can quantify investment consequences, NOT manufacture new independent OOS. No bad-asset dropping, hindsight filters, fee reduction, chosen best parameter, new signal, risk lever > 1x notional, 2026 holdout opening, "approved machine" claim.
- No main branch changes, no PR merge, no capital, live/dry orders, private credentials, account/wallet reads, exchange mutation, funded services or deployment.
