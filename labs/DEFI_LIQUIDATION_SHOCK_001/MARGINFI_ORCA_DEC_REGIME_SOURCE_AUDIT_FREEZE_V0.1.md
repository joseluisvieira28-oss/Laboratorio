# DLS — MARGINFI ORCA DECEMBER REGIME SOURCE AUDIT V0.1 — FREEZE

Date: 2026-10-01
Branch: dls-marginfi-orca-dec-regime-v01
Status: SOURCE/FEATURE-ONLY DIAGNOSTIC; NO 2025 MARKET OUTCOMES

Purpose:
Explain the source/feature regime change observed across Oct-Nov-Dec 2024 without using any 2025
price, return, PnL or trading result.

Authorities:
- Oct-Dec Orca source PASS:
  run 36814861360
  artifact 11140129257
  digest sha256:8d8b1b9fdf84dcc234e46012a39cc5126fa5b3068e739daf1f5d7e83ee42a4d7
- Oct-Dec feature-only artifact:
  run 36815199005
  artifact 11140992589
  digest sha256:b452730607f3db4c7f983ce748c74be1ee7f7a51301a1f3876e7d62698cac470

The audit is descriptive. It may be motivated by the terminal OOS result, but it MUST NOT read that
OOS ledger or any market return.

Frozen monthly diagnostics for October, November, December:

Event-level:
- direction-proven Orca event count
- exact sold SOL sum, mean, median, p25, p75, p90, p95, max
- liability mint frequency and top-1/top-3 share
- route length frequency
- Orca instruction-type frequency

Cascade-level, from the existing feature-only rows:
- cascade count
- distinct decision days
- source events per cascade distribution
- cascade_sold_sol sum/mean/median/p25/p75/p90/p95/max
- pre5m_base_volume_sol mean/median/p25/p75/p90/p95/max
- flow_turnover_intensity mean/median/p25/p75/p90/p95/max
- share above the old absolute Jul-Sep top-quartile threshold 1.252336612578286e-05

Concentration:
- top day share of cascade_sold_sol
- top 2 days share of cascade_sold_sol
- top cascade share of cascade_sold_sol
- top 5 cascades share of cascade_sold_sol

Cross-month descriptive ratios:
- Dec/Nov and Dec/Oct median event sold SOL
- Dec/Nov and Dec/Oct median cascade sold SOL
- Dec/Nov and Dec/Oct median pre5m turnover
- Dec/Nov and Dec/Oct median flow-turnover intensity

No outcome-derived filtering is allowed.

Classification:
MARGINFI_ORCA_DEC_REGIME_SOURCE_AUDIT_PASS
only if:
- canonical source classification is PASS
- canonical feature artifact firewall proves OHLC/returns/PnL were not read
- all 2,263 direction-proven source rows are accounted for
- all 77 feature cascades are accounted for
- no invalid/nonpositive exact sold amount
- no invalid/nonpositive feature denominator/intensity

Otherwise:
MARGINFI_ORCA_DEC_REGIME_SOURCE_AUDIT_BLOCKED

This audit does NOT establish a trading edge and does not authorize 2025 market outcomes.

Firewall:
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
