# LCOD CANONICAL CURVE BASELINE-THRESHOLD CONSISTENCY ADDENDUM V0.1B

Frozen: 2026-09-25
Parent: LCOD_CANONICAL_COLLATERAL_STRESS_CURVE_FREEZE_V0.1
Canonical curve values seen before this addendum: NO.

The liquidation boundary HF=1 is discontinuous. A reconstruction can satisfy
the numeric <=5e-5 relative-error source tolerance yet theoretically land on the
opposite side of HF=1 from official getUserAccountData.

To prevent a numerical boundary artifact from being counted as a mechanical
stress crossing:

- baseline underwater authority remains official HF_N < 1e18;
- every INCLUDED baseline-healthy pair (official HF_N >= 1e18) must also have
  reconstructed HF_N >= 1e18 before it may participate in newly-eligible
  crossings;
- if any included baseline-healthy pair has reconstructed HF_N < 1e18,
  classify CANONICAL_CURVE_SOURCE_BLOCKED with reason
  BASELINE_THRESHOLD_SIDE_DISAGREEMENT.

No tolerance widening or epsilon band is permitted after data are opened.

Baseline-underwater borrowers are counted from official HF only and cannot
become newly eligible because they are already below the protocol boundary.

This is a deterministic source/numerical-consistency rule, not a predictor.
