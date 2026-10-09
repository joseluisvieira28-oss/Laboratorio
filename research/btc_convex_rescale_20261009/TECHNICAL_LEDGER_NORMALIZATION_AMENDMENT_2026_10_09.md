# TECHNICAL LEDGER NORMALIZATION AMENDMENT — NO SCIENTIFIC CHANGE

Initial frozen sizing test run 37893743955 attempted to access `trades[].qty` and correctly failed before computing/evaluating any exposure arm, with `RESIZE_FAIL_CLOSED KeyError('qty')`. Archived original Parent V5 receipt trade dictionaries have entry price, exit price, total both-side commission, and `return_pct`, but do not persist `qty`.

**Technical recovery, same frozen science:** original per-trade net notional return is explicitly stored in original market simulator as `trade["return_pct"] = 100 * trade["net_pnl"] / (qty * trade["entry"])`. Use `trade["return_pct"]/100` as the *unchanged original* per-notional return. Reconstruct quantity for independent reconciliation using `qty=trade["commission"] / (0.001 * (trade["entry"]+trade["exit"]))`, because original fee is exactly 0.001 per side, using executed entry/exit prices; compare recovered implied `net_pnl / (qty*entry)` with saved `return_pct /100`. If missing, zero/negative qty, nonfinite or discrepancy: fail closed. Synthetic test may explicitly include qty and no commission.

No changes to source artifacts, prior outcomes, BASE/STRESS costs, exposure arms (95%, 6.25%, 12.5%, 25%), initial 4% stop, top3-missing experiment, +10bps surcharge, account or instrument universe, capital, classification, or execution assumptions.

Run 37893743955 has no computed edge verdict and must never be counted as PASS or FAIL. Correcting a missing-quantity serialization mismatch does not itself promote the underlying historical strategy.
