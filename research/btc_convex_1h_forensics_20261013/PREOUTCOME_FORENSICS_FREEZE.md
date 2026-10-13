# BTC-CONVEX 1H — ECONOMIC FORENSICS / EXIT-PROTECTION PRE-OUTCOME CONTRACT V0.1
Frozen UTC 2026-10-13, separate from the known-market 2021–2025 prior exercise.
Authority: research-only; no merge to main, live trading, orders, exchange mutations, private APIs, accounts, wallets, spend, Render or protected 2026 holdout.

## Immutable historical source
Analyze **ONLY** the already executed and immutable completed run:
- GitHub Actions run 38426153613, artifact 11828479302 `BTC-CONVEX-5M-CANONICAL-4TF-V02-DESCRIPTIVE-NO-OOS`
- SHA of parent source and immutable Parent V5: leave completely unchanged
- 1h_BASE_TRADES.csv, 1h_STRESS_TRADES.csv, MATRIX_RESULTS.json, official-publisher-checksummed source manifests.
- Expected BASE: 77 closed trades, starting paper 10,000 USDT, terminal marked +15.074361072%, fee 278.22355543339734 USDT, funding -1154.2604487567478 USDT, 2021–25.
- Expected STRESS: 78 closed trades, +13.607362114% marked, fees 280.43153046393576 USDT, funding -1149.3581925737353 USDT.
Do NOT download any additional outcomes and do NOT retune historical entries, stops, trailing or chosen timeframe.

## Predeclared F1—F4 frozen analyses (NO new alpha outcome)
F1. Accounting reconciliation: entries, exits, price PnL, fees, funding cashflow, net PnL, annual contributions, entry/exit monthly cohort, gross winning trades, top1/3/5/10 net winners, top1/3 biggest losses, return on notional, holding durations, 2024 concentration; check every row that `net_pnl == price_pnl-entry_fees-exit_fee+funding`. Check ledger sum reconciles realized cash and expected fees/funding. The existing portfolio includes **a final still-open position**, so total portfolio fee/funding need NOT equal sums of closed trade contributions; quantify residual and mark as OPEN_POSITION_RESIDUAL, not missing data.
F2. COST BOUNDARY COUNTERFACTUALS: on **unchanged closed trade ledger** sum components under these strictly accounting-only cases: as-recorded, zero fee, zero funding, zero both, plus hypothetical additional +2/+5/+10 basis points per side (compute from observed fixed entry and exit notionals), and nominal 50% reduction in taker fees. These are *static fixed-trade PnL adjustments* ONLY; they do not generate a valid dynamic portfolio, future fees/marks or proof of maker-limit fills. 0-fee/0-funding is an unrealistic ceiling. No parameter sweep over candidate signals, exit levels or asset; fixed cost sensitivity is an economic falsification.
F3. FUNDING PROVENANCE / RISK: Funding from earlier canonical 5m market-open proxy (NOT exact settlement mark), 5,478 archived rates. Quantify realized funding net and its concentration by trade, year, holding length; count when funding is cost versus credit. To claim actual settlement, source exact mark and time-matched funding snapshots and contract venue fee proofs would be required. No funding avoidance strategy or futures leverage inferred here.
F4. PAYOFF CONCENTRATION / EXIT PROTECTION PRIORITY: Top3 winner removal on unchanged ledger (NOT a valid rebalance). Determine whether protection against giveback can be justified by **future price-path custody**, not historical stop optimization. Freeze future candidate concept separately (see below); DO NOT simulate alternate historical stops to pick winner on the already-known BTC period.

## New separate forward hypothesis, NOT implemented/activated by forensic diagnostics
Forward child `BTC-CONVEX-1H-NONLATCHEXIT-AUDIT-001`: identical original 1H confirmed-bar long entries. Compare original nonlatched 4% stop/12% trailing activated when completed-bar profit >=5% against a separate new **no-reset post-profit stop** control: once a completed 1h close ever first reaches +5%, permanently preserve max(existing stop, initial stop) over the remaining trade. This is *not* a novelty claim: prior H1 sticky trail tested/failed for other settings; before promotion reconcile historical H1 and existing matches to avoid duplicate mining. Fixed thresholds unchanged and no historical parameter selection, separate single-slot paper books on identical future events. This is a source/exit-integrity comparison only until new genuine forward outcomes.
Minimum future credit: contemporaneous append-only price/decision/stop records with public executable bid/ask plus funding/mark, no retrospective scraping as forward, same risk budget and matched 1h opportunities. No collector or live authority claimed merely by writing a contract.

## Gates
Reject artifact mismatch, missing 1h BASE/STRESS ledgers, unknown CSV schemas, duplicate/overlapping individual trade timestamps per arm, nonfinite price/qty/fee/PnL, cash ledger mismatch, missing open position residual attribution. No independent OOS credit for old BTC history. Keep diagnostic cost sensitivity independent of forward validation. If no verified data/permission, SOURCE_BLOCKED; never invent a result.
