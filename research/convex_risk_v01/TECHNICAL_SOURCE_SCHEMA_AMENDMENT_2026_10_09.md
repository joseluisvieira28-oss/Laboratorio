# V0.1 technical source-schema amendment — 2026-10-09

Fail-closed original workflow run: 37896476055; synthetic invariants PASS, original canonical artifacts downloaded, trade source reader failed at `KeyError: 'qty'`. This is a **technical schema mismatch**, not a scientific result.

The original preserved `cross_asset_cost_validation_v0_1.py` / `expansion_cost_validation_v0_1.py` / `h2_third_basket_validation_v0_1.py` trade record excludes `qty` and includes `return_pct=100*net_pnl/(position["qty"]*position["entry"])` at construction. Therefore **the exact same net per-notional is archived as `return_pct/100`**; reference this frozen original formula, do not infer or invent qty. Confirm all `return_pct` finite and signed consistently with `net_pnl`.

Allowed technical repair: replace net per notional `net_pnl/(qty*entry)` by `return_pct/100`; keep all frozen risk budgets, slippage layers, portfolios, missing-top-winner stress and historical data unchanged. Update synthetic fixture to contain exact archived field.

If BASE/STRESS historical signal/stop fill sequences diverge due to different slip affecting stops, record layer-specific chronological original trade sets (each source's entry and exit immutable); still compute original BASE top3 identity by entry timestamp for adversarial removal on each layer and record unmatched counts; never fabricate a cross-layer trade match. Any unmatched top3 must fail closed unless method explicitly pre-defined before rerunning. No independent historical edge promotion from this technical correction.
