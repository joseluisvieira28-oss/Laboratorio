# DLS — MARGINFI ORCA FLOW-RESPONSE DOSE-RESPONSE V0.1 — PRE-OUTCOME FREEZE

Date: 2026-10-01
Branch: dls-marginfi-orca-dose-response-v01
Status: FROZEN BEFORE JUL-SEP 2024 OHLC / RETURNS / PNL

Family:
DLS-MARGINFI-ORCA-FLOW-RESPONSE-001

## Purpose

Test whether the magnitude of source-proven Marginfi forced SOL selling executed through Orca Whirlpools,
relative to immediately preceding SOLUSDT perpetual turnover, has a monotonic relationship with the
next-minute SOLUSDT market response.

This is a market-response discovery family, not yet a trading strategy.

It is materially distinct from the terminal threshold families:
- Jupiter simple continuation: NO_EDGE
- Jupiter post-cascade reversion: NO_EDGE
- Jupiter flow-turnover Q90 continuation: NO_EDGE
- Jul-Sep Jupiter Q90 rebound: PRE-OUTCOME INSUFFICIENT SAMPLE
- Jul-Sep Orca Q90 rebound: PRE-OUTCOME INSUFFICIENT SAMPLE

No threshold is optimized in this family.

## Source authority

Canonical full Orca Jul-Sep source PASS:
- run 36780139559
- artifact ID 11127536853
- digest sha256:4cbe2bad99237aee32d1e21c5055b17258897df6c312639678e68f15c4ae8dcb
- classification MARGINFI_ORCA_JULSEP_SIGNED_FLOW_SOURCE_PASS
- population 8,857
- Orca presence 7,744
- direction proven 7,717
- exact route input amount proven 7,717
- contradictions 0

Eligible event:
- classification = DIRECTION_PROVEN
- route_semantic = COLLATERAL_TO_LIABILITY_ORCA_PROVEN
- asset_label = SIGNED_SELL_PRESSURE_PROVEN
- asset mint = wrapped/native SOL
- exact_route_input_amount > 0

## Source-only cascade and feature authority

Reuse the already-computed source + pre-entry-volume artifact from the pre-outcome Orca Q90 gate:

run 36781289721
artifact ID 11127324942
digest sha256:8dfa5ef296ea65b4e51b46136cd6387b5d0586748ee081737d1ded101c182c87

This artifact intentionally read base-asset volume only and did NOT read OHLC, returns or PnL.

It contains:
- 192 source cascades
- 36 distinct UTC decision days
- July cascades = 71
- August cascades = 86
- September cascades = 35

Frozen feature definition:
flow_turnover_intensity =
cascade_sold_sol / prior-five-complete-minute Binance USDT-M SOLUSDT base-asset volume

Frozen cascade linkage:
5 minutes exactly, unchanged.

Decision time:
A = first full UTC minute strictly after the final source event in the cascade.

No Q90 selection is applied.
All feature-valid cascades are used, subject only to the funding firewall below.

## Funding/confound firewall

Exclude a cascade if [A, A+1m] contains a standard Binance perpetual funding timestamp:
00:00 UTC, 08:00 UTC or 16:00 UTC.

No other time-of-day filter is allowed.

## Frozen market response

Historical price authority:
Binance public USDT-M SOLUSDT perpetual 1-minute daily klines.

Required archive integrity:
- published CHECKSUM SHA256 PASS
- timestamps unique and monotonic
- A and A+1m bars present

Response:
r_1m = OPEN(A+1m) / OPEN(A) - 1

No fees or slippage are subtracted because this family tests market response, not executable profitability.

## Primary statistic

Primary monotonic association:
Spearman rank correlation rho between:

X = flow_turnover_intensity
Y = r_1m

Ties use average ranks.

The sign is NOT preselected:
- rho < 0 indicates stronger forced flow is associated with stronger immediate continuation/downward response
- rho > 0 indicates stronger forced flow is associated with stronger immediate exhaustion/rebound

This is a two-sided relationship discovery.

## Frozen temporal folds

F1:
July + August 2024

F2:
September 2024

Both folds use the same X and Y definitions.

## Frozen robustness test 1 — UTC-day block bootstrap

20,000 replicates
seed = 26100101

Resample complete UTC decision-day blocks with replacement.

For each replicate compute overall Spearman rho.

95% percentile CI.

## Frozen robustness test 2 — extreme-rank contrast

Using all analyzable cascades after the funding firewall:

q = floor(N / 4)

Bottom group:
q lowest X observations.

Top group:
q highest X observations.

Effect:
delta_Q = mean(Y_top) - mean(Y_bottom)

Interpretation:
- delta_Q < 0 = stronger flow has more negative response
- delta_Q > 0 = stronger flow has more positive response

Block-bootstrap delta_Q by UTC day:
20,000 replicates
seed = 26100102

Group membership is fixed from the full-sample X ranking before bootstrap.
No outcome participates in group definition.

## Frozen discovery gate

Classification:

MARGINFI_ORCA_FLOW_RESPONSE_DISCOVERY_PASS

only if ALL:

1. analyzable N >= 150
2. distinct UTC days >= 30
3. F1 N >= 120
4. F2 N >= 30
5. abs(overall Spearman rho) >= 0.15
6. Spearman day-block bootstrap 95% CI excludes 0
7. F1 rho and F2 rho have the same non-zero sign as overall rho
8. abs(F1 rho) >= 0.05
9. abs(F2 rho) >= 0.05
10. top-vs-bottom quartile delta_Q has the same sign as overall rho
11. delta_Q day-block bootstrap 95% CI excludes 0

If source or market integrity fails:
MARGINFI_ORCA_FLOW_RESPONSE_SOURCE_BLOCKED

Otherwise:
MARGINFI_ORCA_FLOW_RESPONSE_NO_RELATIONSHIP

## Consequence of PASS

PASS does NOT authorize live trading.

PASS authorizes a separately frozen executable validation family in the untouched period:

[2024-10-01T00:00:00Z, 2025-01-01T00:00:00Z)

The future trading direction MUST be the sign discovered here:
- negative relationship -> future SHORT rule
- positive relationship -> future LONG rule

Any future threshold must be frozen without using Oct-Dec outcomes.

## Forbidden rescue

After Jul-Sep outcomes are opened, V0.1 may NOT:
- change response horizon
- inspect/select 2m/3m/5m/15m responses
- change feature denominator
- change 5-minute cascade linkage
- add Q90 or another threshold to rescue the relation
- delete September
- change temporal folds
- replace Spearman with a favorable statistic
- change rho minimum
- change bootstrap seeds/gates
- create a Jul-Sep trading rule from the observed direction

Jul-Sep is discovery only.
If PASS, trading validation moves forward to untouched Oct-Dec.

## Firewall

jul_sep_market_outcomes_opened_after_freeze=true
jul_sep_trading_validation=false
oct_dec_2024_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
