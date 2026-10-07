# BTC-OPTIONS-VRP-001 — LINEAR USDC FORWARD ENTRY SOURCE BANK V0.1
Date: 2026-10-07
Status: FROZEN SOURCE-ONLY / OUTCOME-SEALED

## Objective
Build the missing prospective executable-entry source corpus for BTC_USDC linear options at the operator-accessible 0.01 contract size.

This is NOT an economic test.

## Schedule
One capture per eligible Thursday at 08:05 UTC, beginning 2026-10-08.
Valid operational window: Thursday 08:00:00–08:15:00 UTC.
No backfill. A missed Thursday is preserved as missed.

## Frozen selection
At capture time:
1. Deribit public unauthenticated BTC_USDC option instruments only;
2. expiries 14–60 DTE;
3. choose expiry nearest 30 DTE, earlier expiry tie-break;
4. choose same-strike call+put nearest log-moneyness to current BTC_USDC index;
5. amount reference = 0.01 contract each leg;
6. require bid size >=0.01 on call and put;
7. record best bid/ask price+size, bid/ask/mark IV, mark/index/underlying, Greeks and source timestamps;
8. record BTC_USDC-PERPETUAL best bid/ask and source timestamp as hedge-source witness.

## Integrity
Per-request request_start_ms and response_received_ms are mandatory.
Source timestamp freshness at receipt must be <=30 seconds.
Append-only one key per UTC capture date.
Duplicate exact date fails closed.
Malformed existing ledger fails closed.

## Outcome seal
During source banking:
- no delivery/settlement price is fetched;
- no future BTC path is fetched;
- no realized variance;
- no option payoff;
- no hedge return;
- no PnL/return/expectancy;
- no win/loss label.

Settlement is deliberately deferred because public historical delivery prices can be retrieved after a future activation freeze.

## Readiness
No universal N is declared here.
The bank reports only raw clean entry count, date span, DTE distribution, BBO spreads, quoted size and source integrity.

Opening economic outcomes requires a separate V2 activation freeze with:
- defined executable MVE;
- capital/risk denominator;
- costs/fees;
- H and theta_design;
- ex-ante power or sequential evidence rule;
- multiplicity policy;
- untouched outcome boundary.

## Safety
No authentication, orders, account reads, wallets, payment, live trading, exchange mutation or main merge.
