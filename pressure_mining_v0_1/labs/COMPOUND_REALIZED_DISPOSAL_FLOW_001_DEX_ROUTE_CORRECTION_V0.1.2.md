# COMPOUND-REALIZED-DISPOSAL-FLOW-001 — DEX ROUTE METRIC CORRECTION V0.1.2

Date: 2026-09-28
Status: TECHNICAL CORRECTION ONLY / SCIENCE UNCHANGED

V0.1.1 correctly changed the route-status formula to use the onward intersection but a source-edit omission left `recognized_onward` unincremented and left the displayed onward percentage on the old numerator. The workflow correctly failed its invariant check.

V0.1.2 fixes only those two implementation defects.

Scientific invariants remain unchanged:
- exact same frozen 64 transactions;
- exact same 68 BuyCollateral events in those transactions;
- exact same recognized DEX event ABI signatures;
- exact same >=60% route-evidence threshold;
- no prices, swap amounts, returns, PnL or 2025 market outcomes.

New hard validation:
- recognized_onward <= onward <= inferred;
- displayed onward percentage must remain in [0,100].

V0.1 and V0.1.1 remain immutable technical evidence and must not be used as the final classification.
