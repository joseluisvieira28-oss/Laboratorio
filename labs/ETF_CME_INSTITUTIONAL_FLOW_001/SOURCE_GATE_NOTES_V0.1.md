# ETF-CME-INSTFLOW-001 — SOURCE/DATA GATE NOTES V0.1

Outcome-blind validation of CFTC Legacy Futures Only dataset `6dca-aqww`, CME Bitcoin contract code `133741`, 2018-01-01 through 2024-12-31 only.

Hard checks: exact market code; required source-native fields; positive open interest; non-negative non-commercial positions; unique report dates; exact 7-day report cadence; >=300 parsed rows; no 2025/2026 access; no signals, returns, outcomes, or PnL.

Fail-closed classification: any issue => `SOURCE_DATA_GATE_BLOCKED`; never reinterpret infrastructure/data failure as NO_EDGE.
