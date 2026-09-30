# DLS — MARGINFI SOL FLOW-MAGNITUDE REVERSION V0.1 — PRE-OUTCOME FREEZE

Date: 2026-09-30
Branch: dls-marginfi-flow-magnitude-v01
Status: FROZEN BEFORE APR-JUN 2024 MARKET OUTCOMES

Family:
DLS-MARGINFI-SOL-FLOW-MAGNITUDE-REVERSION-001

## Motivation boundary

Prior families established:
- source-proven Marginfi SOL sell pressure exists;
- unconditional 5-minute continuation failed in Jan-2024;
- unconditional post-cascade 15-minute reversion failed in Feb-Mar 2024.

This family tests a materially distinct hypothesis:
only unusually large source-realized SOL sell cascades may create transient impact large enough to mean-revert.

Jan-2024 and Feb-Mar-2024 market returns are discovery history only.
They are prohibited from validation statistics for this family.

## Frozen source calibration

Calibration source window:
[2024-02-01T00:00:00Z, 2024-04-01T00:00:00Z)

Canonical source authority:
MARGINFI_SOL_FEBMAR_SIGNED_FLOW_SOURCE_PASS
run 36589912203 attempt 2
artifact ID 11053637340
digest sha256:8100803148ead42807322446fcbf9f7c678b6a6589e0c4509f4ddcf930afab3d

Eligible source event:
- classification = DIRECTION_PROVEN
- route_semantic = COLLATERAL_TO_LIABILITY_MULTI_HOP_PROVEN
- asset_label = SIGNED_SELL_PRESSURE_PROVEN
- asset_mint = So11111111111111111111111111111111111111112

Realized SOL amount per event:
- use decoded_swap_events[0].inputAmount only;
- route_input_mint must equal native wrapped SOL mint above;
- inputAmount must be positive integer;
- SOL decimals fixed at 9;
- realized_sol = inputAmount / 1e9.

No requested instruction quantity, token-output quantity, USD conversion, price, return or PnL may enter amount calibration.

## Frozen cascade construction

Exactly the already-frozen source-only rule:
- sort eligible events by timestamp, signature, canonical instructionAddress;
- start a new cascade at the first event;
- a following event joins the active cascade iff its timestamp is <= 5 minutes after the immediately previous eligible event timestamp;
- otherwise close the cascade and start a new one.

Cascade realized amount:
sum(realized_sol) across exact member events.

## Frozen magnitude threshold

Compute empirical Q75 from ALL Feb-Mar source cascades using nearest-rank:

rank = ceil(0.75 * N)
threshold = sorted_cascade_amounts[rank - 1]

No interpolation.
No market outcome is read.
Ties at the threshold are included.

This numeric threshold becomes immutable before Apr-Jun prices open.

## Fresh source-validation window

Apr-Jun source window:
[2024-04-01T00:00:00Z, 2024-07-01T00:00:00Z)

Before any Apr-Jun market price is opened:
- acquire exact Marginfi field-enrichment partitions 202404, 202405, 202406;
- retain only native-SOL collateral liquidations;
- require exact same Marginfi account-role semantics;
- require exact post-liquidation Jupiter route ownership;
- decode realized SwapEvent chain with the same V0.2 multi-hop semantics;
- require route_input_mint = SOL and route_output_mint = liability mint;
- contradictions = 0.

Source PASS requires:
- source completeness >= 95% among Jupiter route members;
- deterministic direction >= 90% among source-complete members;
- contradictions = 0.

If source gate fails, market experiment MUST NOT run.

## Frozen Development rule

Development source and market window:
[2024-04-01T00:00:00Z, 2024-07-01T00:00:00Z)

Construct cascades exactly as above.
Select only cascades with total realized SOL >= frozen Feb-Mar Q75 threshold.

For every selected completed cascade:

A = first full UTC minute strictly after last_event_time.

Enter:
LONG SOLUSDT at OPEN of minute A.

Exit:
OPEN of minute A + 15 minutes.

Only one trade per selected cascade.
No pyramiding.
If a selected cascade would enter before an existing position exits, ignore the later candidate.

## Funding firewall

Exclude any candidate whose [entry, exit] interval includes:
00:00 UTC, 08:00 UTC, or 16:00 UTC.

## Market-data authority

Binance public USDT-M SOLUSDT perpetual 1-minute daily archives.
Each archive must pass published CHECKSUM SHA256 and timestamp integrity.

## Frozen costs

Primary:
- MEXC Futures API taker = 8 bps/side
- slippage = 2 bps/side
- approximately 20 bps round trip

Stress descriptive only:
- same taker fee
- slippage = 5 bps/side
- approximately 26 bps round trip

Primary classification uses nominal only.

## Frozen Development gates

SURVIVES only if ALL:
1. analyzable trades >= 20
2. distinct UTC entry days >= 10
3. nominal mean > 0
4. nominal median > 0
5. nominal profit factor > 1.10
6. April trades >= 5
7. May trades >= 5
8. June trades >= 5
9. April nominal mean > 0
10. May nominal mean > 0
11. June nominal mean > 0
12. UTC-day block-bootstrap 95% CI lower bound of nominal mean > 0

Bootstrap:
- 20,000 replicates
- whole UTC entry-day blocks
- seed 26093075

Terminal labels:
- MARGINFI_SOL_FLOW_MAGNITUDE_DEVELOPMENT_SURVIVES
- MARGINFI_SOL_FLOW_MAGNITUDE_DEVELOPMENT_NO_EDGE
- MARGINFI_SOL_FLOW_MAGNITUDE_DEVELOPMENT_SOURCE_BLOCKED

## Future boundary

Only if Development SURVIVES:
OOS candidate = [2024-07-01, 2024-10-01)

Only if OOS survives:
holdout candidate = [2024-10-01, 2025-01-01)

2025/2026 remain closed.

## Forbidden rescue

After Apr-Jun outcomes open, V0.1 may NOT:
- change Q75 to Q50/Q90/top-N;
- use USD notional;
- change 5-minute cascade linkage;
- change LONG side;
- change 15-minute hold;
- add liability-mint/hop-count/time-of-day filters;
- change primary costs;
- remove losing months/days;
- optimize entry delay;
- use Jan or Feb-Mar returns as validation;
- open Jul-Sep unless Development SURVIVES.

## Firewall

source_calibration_prices=false
source_calibration_returns=false
apr_jun_market_outcomes_opened_after_freeze=true
jul_sep_oos_opened=false
oct_dec_holdout_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
