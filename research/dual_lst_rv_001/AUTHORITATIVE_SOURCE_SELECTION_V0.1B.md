# DUAL-LST-RV-001 — AUTHORITATIVE SOURCE SELECTION V0.1B

Frozen: 2026-09-27

## Authority

Only the following source result may become authoritative for DUAL-LST-RV-001:

- script: research/dual_lst_rv_001/dual_lst_source_probe_v01b.mjs
- receipt: DUAL_LST_RV_001_SOURCE_GATE_RECEIPT_V0.1B.json
- authority documents:
  - SOURCE_DATA_GATE_FREEZE_V0.1.md
  - SOURCE_GATE_HARDENING_ADDENDUM_V0.1A.md
  - COMMON_NUMERAIRE_ADDENDUM_V0.1B.md

## Superseded diagnostic

The original V0.1 workflow/run may still complete because it was queued before V0.1A/V0.1B hardening.

Any receipt from:
dual_lst_source_probe_v01.mjs

is DIAGNOSTIC_ONLY and earns zero scientific/promotion credit.

It may not authorize downstream work because it:
- did not require the direct pool to pass all four sentinels;
- did not prove the common Lido protocol-accounting ETH numeraire at every sentinel;
- did not use the hardened one-call-per-block Multicall3 + EIP-1898 blockHash path.

## Downstream firewall

No downstream predictor census, threshold, direction, convergence outcome, PnL or trading work may open unless:

DUAL_LST_RV_001_SOURCE_GATE_RECEIPT_V0.1B.json
exists durably and
classification == SOURCE_PASS.

No V0.1 diagnostic PASS may substitute for V0.1B.

Promotion credit = 0.
