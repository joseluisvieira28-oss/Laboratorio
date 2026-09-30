# DLS — MARGINFI ORCA ROUTE-SPECIFIC REBOUND V0.2 — BALANCED TEMPORAL DEVELOPMENT FREEZE

Date: 2026-09-30
Branch: dls-marginfi-orca-route-rebound-v02
Status: FROZEN BEFORE OCT-DEC 2024 MARKET OUTCOMES

Family:
DLS-MARGINFI-ORCA-ROUTE-REBOUND-002

## Context

V0.1 closed PRE-OUTCOME because its fixed calendar folds produced 61 candidates in Oct-Nov and 16 in
December versus a frozen F2 minimum of 20.

No Oct-Dec OHLC, return or PnL was opened.

V0.2 keeps the market hypothesis unchanged and replaces only the temporal robustness partition with an
outcome-blind chronological balanced split derived solely from source timestamps.

## Canonical source

MARGINFI_ORCA_OCTDEC_SIGNED_FLOW_SOURCE_PASS

run 36782337541
artifact 11127978050
digest sha256:fab18e89882fb13d5dcbd59ce16fc453f114959688d689d9892d191f8098184a

Source facts:
- 2,688 canonical SOL liquidations
- 2,263 Orca presence
- 2,263 source complete
- 2,263 direction proven
- 0 ambiguous
- 0 contradictions

## Frozen event and cascade rules

Eligible event:
- classification = DIRECTION_PROVEN
- route_semantic = COLLATERAL_TO_LIABILITY_ORCA_PROVEN
- asset_label = SIGNED_SELL_PRESSURE_PROVEN
- asset mint = wrapped/native SOL

No amount threshold.
No Q90.
No liability/instruction/hop/time filter.

Cascade:
sort by timestamp, signature, canonical instructionAddress.

A subsequent event joins the current cascade iff its timestamp is <=5 minutes after the immediately
previous eligible event timestamp.

Decision time:
A = first full UTC minute strictly after cascade last_event_time.

Candidate interval:
[A, A+1m]

Funding exclusion:
exclude if interval contains 00:00 UTC, 08:00 UTC or 16:00 UTC.

## Frozen balanced temporal folds

After the above source-only candidate construction and funding exclusion:

1. sort candidates by:
   entry time, then cascade ID;
2. let N be candidate count;
3. let K = floor(N / 2);
4. first K chronological candidates = F1;
5. remaining N-K candidates = F2.

This rule is frozen before market outcomes.

It guarantees no event is selected or assigned using price or return.
The purpose is a balanced first-half / second-half temporal robustness check rather than dependence on
calendar-month event density.

## Mandatory pre-outcome sample gate

Before any OHLC/return/PnL is read:

READY only if ALL:
- N >= 60
- distinct UTC candidate days >= 8
- F1 >= 30
- F2 >= 30

Otherwise:
MARGINFI_ORCA_ROUTE_REBOUND_V02_PREOUTCOME_INSUFFICIENT_SAMPLE

and market outcomes remain closed.

## Frozen market hypothesis

Only after READY:

side = LONG SOLUSDT

Historical research market authority:
Binance public USDT-M SOLUSDT perpetual 1-minute daily archives.

Entry:
OPEN of minute A

Exit:
OPEN of minute A + 1 minute

Every required daily archive must:
- pass published SHA256 CHECKSUM;
- contain unique monotonic minute timestamps;
- contain every entry/exit minute.

## Frozen costs

Primary:
- MEXC Futures API taker fee 8 bps per side
- slippage 2 bps per side
- approximate round-trip 20 bps

Stress descriptive only:
- same fee
- slippage 5 bps per side
- approximate round-trip 26 bps

Primary classification uses nominal only.

No maker assumption, rebate, fee discount or leverage benefit.

## Frozen Development gates

MARGINFI_ORCA_ROUTE_REBOUND_V02_DEVELOPMENT_SURVIVES only if ALL:

1. analyzable n >=60;
2. distinct UTC entry days >=8;
3. nominal net mean >0;
4. nominal net median >0;
5. nominal net profit factor >1.10;
6. F1 n >=30;
7. F2 n >=30;
8. F1 nominal net mean >0;
9. F2 nominal net mean >0;
10. UTC-day block-bootstrap 95% CI lower bound of nominal mean >0.

Bootstrap:
- 20,000 replicates
- complete UTC entry-day blocks
- seed 26093006

Otherwise:
MARGINFI_ORCA_ROUTE_REBOUND_V02_DEVELOPMENT_NO_EDGE

Integrity failure:
MARGINFI_ORCA_ROUTE_REBOUND_V02_DEVELOPMENT_SOURCE_BLOCKED

## Future boundary

2025/2026 market outcomes remain CLOSED.

Only if Development SURVIVES may a separately frozen OOS family be designed.

## Forbidden rescue

After outcomes open:
- no side flip
- no alternate hold
- no amount/Q90 filters
- no liability/instruction/hop/time filters
- no event deletion
- no cost change
- no fold-rule change
- no gate change
- no 2025 rescue

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
