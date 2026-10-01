# MARGINFI ORCA FLOW-RESPONSE V0.1 — DISCOVERY PASS CLOSEOUT

Date: 2026-10-01
Branch: dls-marginfi-orca-dose-response-v01

Family:
DLS-MARGINFI-ORCA-FLOW-RESPONSE-001

Canonical discovery run:
36814416648

Canonical artifact:
dls-marginfi-orca-flow-response-v01
artifact ID 11140333264
digest sha256:df7e37d1b2ea23052589802cda1d0b0dc37921bae3a1c23fe6dd3bd2fd614162

Classification:
MARGINFI_ORCA_FLOW_RESPONSE_DISCOVERY_PASS

Analyzable cascades:
191

Distinct UTC days:
35

Funding-excluded:
1

Overall Spearman rho:
+0.2806386056764949

F1 Jul-Aug:
n=157
rho=+0.26730195548223445

F2 September:
n=34
rho=+0.2055003819709702

UTC-day block bootstrap rho, 20,000 replicates:
95% CI = [+0.10959738083216897, +0.36433335124610083]

Frozen top-vs-bottom quartile contrast:
quartile size = 47
bottom quartile mean 1m response = +0.00029603927259659395
top quartile mean 1m response = +0.0022275670785056193
top minus bottom = +0.0019315278059090254

UTC-day block bootstrap top-minus-bottom:
95% CI = [+0.0009593048662427454, +0.0028075244133034024]

Discovered sign:
POSITIVE_REBOUND

All frozen discovery gates PASS.

Market-data integrity:
36 / 36 daily archives PASS
0 missing minutes
0 hard errors

## OOS consequence

Jul-Sep is discovery only and MUST NOT be used for trading validation.

The pre-specified top-quartile group boundary is derived solely from the already-frozen feature ranking:
X >= 1.252336612578286e-05

This numeric boundary is the minimum X among the top floor(N/4)=47 observations after the frozen funding firewall.
It is therefore feature-derived, not outcome-selected.

A future executable validation may use:
- Oct-Dec 2024 only
- Orca signed-flow source semantics unchanged
- same 5-minute cascade rule
- same prior-five-minute Binance base-volume denominator
- signal X >= 1.252336612578286e-05
- side LONG
- hold 1 minute
- primary costs 20 bps round trip
- no tuning on Oct-Dec outcomes

Firewall:
jul_sep_trading_validation=false
oct_dec_2024_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
