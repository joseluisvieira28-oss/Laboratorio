# DLS — MARGINFI ORCA ROUTE-SPECIFIC REBOUND V0.1 — PRE-OUTCOME FREEZE

Date: 2026-09-30
Branch: dls-marginfi-orca-route-rebound-v01
Status: FROZEN BEFORE OCT-DEC 2024 MARKET OUTCOMES

Family:
DLS-MARGINFI-ORCA-ROUTE-REBOUND-001

## Scientific question

Does source-proven forced SOL selling executed through Orca Whirlpools exhibit an immediate one-minute
cross-venue rebound after the liquidation cascade ends, irrespective of flow-size threshold?

Economic mechanism:
Orca Whirlpools is a concentrated-liquidity AMM. A forced sell may transiently move the on-chain route
through local liquidity before arbitrage/replenishment restores cross-venue pricing.

This is a route-specific family.
It is distinct from:
- Jupiter/simple continuation NO_EDGE;
- Jupiter/post-cascade 15m rebound NO_EDGE;
- flow-to-turnover 1m SHORT NO_EDGE;
- thresholded Orca rebound V0.1/V0.2, which both closed PRE-OUTCOME without reading returns.

No Oct-Dec OHLC, returns or PnL have been opened.

## Canonical source authority

MARGINFI_ORCA_OCTDEC_SIGNED_FLOW_SOURCE_PASS

Canonical run:
36782337541

Canonical artifact:
dls-marginfi-orca-octdec-signed-flow-source-v021
artifact ID 11127978050
digest sha256:fab18e89882fb13d5dcbd59ce16fc453f114959688d689d9892d191f8098184a

Source facts:
- canonical SOL population: 2,688
- Orca presence: 2,263
- source complete: 2,263
- direction proven: 2,263
- direction ambiguous: 0
- contradictions: 0
- exact input amount proven: 2,263

## Frozen event eligibility

Use every source row satisfying:
- classification = DIRECTION_PROVEN;
- route_semantic = COLLATERAL_TO_LIABILITY_ORCA_PROVEN;
- asset_label = SIGNED_SELL_PRESSURE_PROVEN;
- asset_mint = So11111111111111111111111111111111111111112.

No amount threshold.
No Q90.
No liability filter.
No instruction-type filter.
No hop-count filter.
No time-of-day filter.
No price/return participates in selection.

Exact input amount is reported but is not required for this family because size is not a signal input.

## Frozen cascade construction

Sort eligible events by:
timestamp, signature, canonical instructionAddress.

Start a cascade at the first eligible event.

A subsequent eligible event joins the current cascade iff its source timestamp is <=5 minutes after the
immediately previous eligible event timestamp.

Otherwise close the cascade and start a new one.

Decision time:
A = first full UTC minute strictly after last_event_time.

Only one candidate trade per cascade.

## Mandatory source-only pre-outcome sample gate

Before any Oct-Dec OHLC/returns/PnL is read:

Apply the frozen funding-time exclusion using timestamps only.

Candidate interval:
[A, A+1m]

Exclude if the interval contains:
00:00 UTC, 08:00 UTC or 16:00 UTC.

PREOUTCOME_READY only if ALL:
1. analyzable candidate count >=40;
2. distinct UTC candidate days >=8;
3. F1 Oct-Nov candidate count >=10;
4. F2 December candidate count >=20.

If any fail:
MARGINFI_ORCA_ROUTE_REBOUND_PREOUTCOME_INSUFFICIENT_SAMPLE

and the family closes without opening outcomes.

## Frozen market rule

Only after PREOUTCOME_READY:

side = LONG SOLUSDT

Historical research price authority:
Binance public USDT-M SOLUSDT perpetual 1-minute daily archives.

Entry:
OPEN of minute A

Exit:
OPEN of minute A + 1 minute

Required market data:
- published daily CHECKSUM SHA256 PASS;
- unique monotonic timestamps;
- every entry/exit minute present.

No pyramiding.
No scaling.
No hold extension.

## Frozen execution costs

Primary:
- MEXC Futures API taker fee = 8 bps per side;
- slippage = 2 bps per side;
- approximate round-trip = 20 bps.

Stress descriptive only:
- same fee;
- slippage = 5 bps per side;
- approximate round-trip = 26 bps.

Primary classification uses nominal only.

No maker fills, rebates, VIP discounts or leverage benefit.

## Development window and folds

Development:
[2024-10-01T00:00:00Z, 2025-01-01T00:00:00Z)

F1:
[2024-10-01T00:00:00Z, 2024-12-01T00:00:00Z)

F2:
[2024-12-01T00:00:00Z, 2025-01-01T00:00:00Z)

## Frozen Development gate

MARGINFI_ORCA_ROUTE_REBOUND_DEVELOPMENT_SURVIVES only if ALL:

1. analyzable trade count >=40;
2. distinct UTC entry days >=8;
3. nominal net mean >0;
4. nominal net median >0;
5. nominal net profit factor >1.10;
6. F1 trade count >=10;
7. F2 trade count >=20;
8. F1 nominal net mean >0;
9. F2 nominal net mean >0;
10. UTC-day block-bootstrap 95% CI lower bound of nominal mean >0.

Bootstrap:
- 20,000 replicates;
- complete UTC entry-day blocks;
- seed = 26093005.

Otherwise:
MARGINFI_ORCA_ROUTE_REBOUND_DEVELOPMENT_NO_EDGE

Integrity failure:
MARGINFI_ORCA_ROUTE_REBOUND_DEVELOPMENT_SOURCE_BLOCKED

## Future boundary

2025 and 2026 market outcomes remain CLOSED.

Only if Development SURVIVES may a separately frozen 2025 OOS source/market family be designed.

## Forbidden rescue

After Oct-Dec outcomes open, V0.1 may NOT:
- add/remove amount thresholds;
- reintroduce Q90 or inspect alternative thresholds;
- change the 5-minute cascade rule;
- flip LONG to SHORT;
- inspect/select other hold horizons;
- filter by liability, instruction type, hop count, date or time;
- change costs;
- change folds or gates;
- open 2025 as rescue after failure.

## Firewall

oct_dec_market_outcomes_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
