# AAVE-RISK-PARAMETER-SHOCK-001 — PRIMARY MECHANISM CENSUS SQD CONTINUATION REMEDIATION V0.1A

Date: 2026-09-18
Status: FROZEN AFTER TECHNICAL FAILURE / BEFORE RERUN
Scope: source/mechanism census only / outcome-blind

## Immutable upstreams

Source Census V0.1A:
- run 35382293497
- artifact 10563606987
- digest sha256:77d74fc89e7078a32147832fc454ba96e1d07a86a4d0aff6c255197b4f7d02f7
- classification SOURCE_CENSUS_PASS
- exact CollateralConfigurationChanged count: 72

Failed primary mechanism census:
- run 35384824276
- artifact 10563377444
- digest sha256:93bfb63768d9f9be942e1303f0dbeb8d570d40be30f790813f42d066a86f924e
- classification MECHANISM_CENSUS_TECHNICAL_OR_PROVENANCE_FAILURE
- failure: decoded/source-census count mismatch: 1 != 72
- transport: 68 requested windows, only 1 matching log decoded

## Root cause

The failed mechanism census advanced its SQD cursor directly to request_to+1 after each HTTP stream response.

SQD stream responses can terminate at an internal continuation block before the requested toBlock. The already-passed Source Census V0.1A correctly advances from the last returned header block + 1, and only advances through the full requested window when the response is a healthy zero-match window.

Therefore the failed mechanism census skipped unreturned portions of requested windows.

## Exact remediation

Change transport continuation only:

- if the SQD response has one or more rows, advance cursor to last returned header block + 1;
- require row block monotonicity and range integrity;
- if the response has zero rows, treat the exact requested window as covered and advance to request_to+1;
- keep requesting log.data because liquidationThreshold decoding is the already-frozen purpose of this census.

Unchanged:
- PoolConfigurator address;
- block envelope;
- timestamp ceiling;
- CollateralConfigurationChanged signature;
- first-per-asset baseline rule;
- decrease definition;
- 24-hour episode independence;
- >=12 episodes;
- >=4 assets;
- >=2 years;
- no magnitude threshold;
- no event-family substitution.

## Firewall

No borrower state.
No LiquidationCall outcomes.
No health factor/overhang.
No market prices/returns/PnL.
No 2025/2026.
No live trading/exchange mutation/main merge.
