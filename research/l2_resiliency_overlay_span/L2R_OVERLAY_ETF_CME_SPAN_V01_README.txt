L2R-OVERLAY-ETF-CME-SPAN-001 — V0.1
==========================================

2025 DEVELOPMENT ONLY.
This is a new LAB_ID after predecessor L2R-OVERLAY-ETF-CME-001 closed as INSUFFICIENT_SAMPLE_OR_SOURCE without observing directional residuals.

Scientific construction:
selected weak L2 event has R observation <= ETF T0 and Y target > ETF T0.
Baseline = frozen midpoint at accepted R observation.
Endpoint = frozen midpoint at accepted Y observation.
PARENT_SPAN_BPS = ETF parent direction * 10,000 * (MID_Y / MID_R - 1).

This is NOT executable ETF fill PnL and NOT independent validation.

Run:
Double-click RUN_L2R_OVERLAY_ETF_CME_SPAN_V01.cmd

Prerequisite:
C:\Users\<you>\Desktop\L2R_2025_BTC_VALIDATION_LOCAL
must contain the canonical L2 2025 corpus.

Expected output:
L2R_OVERLAY_ETF_CME_SPAN_001_2025_DEVELOPMENT_EVIDENCE_V0_1.zip

The first valid outcome-bearing run is immutable.

Firewalls:
NO 2026.
NO live trading.
NO orders.
NO exchange mutation.
NO main merge.
NO cell selection or post-outcome threshold changes.
