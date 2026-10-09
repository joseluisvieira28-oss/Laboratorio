# TECHNICAL LAYER PATH AMENDMENT — NO RETUNING
Two technical fail-closed diagnostics preceded any economically accepted rescale result:
- GitHub run 37893743955: missing archived serialized qty resolved by preserving original trade return_pct and commission reconstruction.
- GitHub run 37893875251: `TRADE_PATH_DIFFERS_BETWEEN_COSTS:SOLUSDT`.

The ORIGINAL frozen parent sim independently re-ran the signal and execution engine with different adverse slippage BASE (2 bps/side) and STRESS (5 bps/side). Because a bar may hit a changed stop, the 2021–25 trade paths, stop exits and subsequent positions may differ. The rescale study must not assume equal length or one-to-one trade identity between separate original frozen BASE and STRESS tapes. The original simulator explicitly stores each layer's independent trade ledger.

**Pure technical correction**: remove the invalid `len(BASE)==len(STRESS)` and per-index entry/exit timestamp equality assertion. Continue validating each **separate** layer's internal chronological order, trade PnL, funding/cost identity, the original 95% capital replay against the **matching original layer** ending equity, and original unchanged source hashes. BASE missed-top3 selection always uses only BASE trade indices; never apply BASE trade indices to the STRESS tape. BASE and STRESS remain reported separately, no overlay picking profitable trades across the two.

Frozen 0.25%,0.50%,1.0% sizing arms; 95% benchmark; 4% initial price stop; all 13 Parent V5 assets; cost stress; missed-top3 rules; scope and verdict language remain unchanged. Original historical data already opened — no independent OOS. Failed prior jobs have no economic credit.
