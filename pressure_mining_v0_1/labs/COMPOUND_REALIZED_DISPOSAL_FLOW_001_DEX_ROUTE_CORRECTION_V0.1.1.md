# COMPOUND-REALIZED-DISPOSAL-FLOW-001 — DEX ROUTE METRIC CORRECTION V0.1.1

Date: 2026-09-28
Status: TECHNICAL CORRECTION ONLY / SCIENCE UNCHANGED

V0.1 run 36380875640 correctly reconstructed the frozen 64-transaction sample and detected recognized DEX swap events, but its displayed "share of onward" denominator used all recognized swap events rather than the intersection of:
- event has same-transaction onward transfer from the inferred recipient; AND
- event has a recognized DEX swap log after BuyCollateral.

This produced an impossible 108.4746% ratio and invalidates only that derived metric and the V0.1 route-status label.

V0.1.1 changes no source, sample, signatures, event decoding, thresholds, or governance rule.
It adds `recognized_dex_swap_on_onward_events` and computes:
recognized_onward / onward.

The V0.1 receipt remains preserved as technical evidence and must not be cited as the final route classification.
