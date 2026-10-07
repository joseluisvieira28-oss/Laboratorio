# BTC-OPTIONS-VRP-001 V2 — LINEAR USDC ACCESSIBILITY SOURCE FREEZE V0.1
Date: 2026-10-07
Status: SOURCE-ONLY / PRE-PROBE / NO PERFORMANCE

## Why this probe exists
The inverse BTC options implementation is operator-accessibility unresolved because the minimum 0.1-contract short straddle requires material Standard Margin capital.

Current official Deribit contract specifications independently establish that BTC_USDC linear options:
- settle/margin in USDC;
- have contract multiplier 1 BTC per contract;
- permit fractional contracts;
- have minimum order size 0.01 contract;
- use Standard Margin formulas defined in USDC.

This source-only probe asks whether the currently listed BTC_USDC option market has a usable point-in-time ATM-ish call/put BBO near 30 DTE at the minimum 0.01 contract size.

## Frozen source query
Unauthenticated public Deribit API only:
- public/get_index_price for btc_usdc;
- public/get_instruments with currency=USDC, kind=option, expired=false;
- retain only instrument names beginning BTC_USDC-;
- public/get_order_book depth=1 for selected legs;
- public/get_order_book depth=1 for BTC_USDC-PERPETUAL if listed.

## Frozen selection
1. active BTC_USDC expiries in 14–60 DTE;
2. choose expiry minimizing |DTE-30|;
3. deterministic tie-break: earlier expiry;
4. within expiry choose same-strike call+put minimizing |ln(strike/index)|;
5. require both call and put;
6. no outcome fields and no future realized return.

## PASS requirements
SOURCE_ACCESSIBILITY_PASS only if:
- BTC_USDC option instruments are currently listed;
- a same-expiry/same-strike call+put pair exists in the frozen DTE envelope;
- both legs have bid and ask;
- bid size on both legs >= 0.01 contract;
- API-reported min_trade_amount <= 0.01 for both legs;
- source timestamps are present;
- no authentication/private endpoint/order/account/wallet is used.

## Outputs allowed
Only source/accessibility facts:
- instrument identity;
- contract_size/min_trade_amount;
- DTE/strike/index;
- bid/ask price and size;
- mark/bid/ask IV when public;
- source timestamp;
- Standard Margin estimate for 0.01+0.01 short pair using official formulas;
- no strategy return, PnL, expectancy, realized variance, hit rate, or outcome.

## Safety
No account.
No KYC action.
No order.
No wallet.
No payment.
No exchange mutation.
No live trading.
No main merge.
