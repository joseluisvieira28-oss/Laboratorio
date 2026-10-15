# 2026-10-15 V06 authenticated account + PUBLIC SOL/BNB contract/risk continuation

**Private user report interpreted locally only; no private account balance, identifiable account information or API secrets committed to the repository.**

## Observed account state (operator-supplied sanitized local V06 receipt)

- Real authenticated private GET requests completed at reported observation time.
- The report's equity and available-balance fields parsed successfully, account reported **HEDGE** (position mode 1), no reported open positions, open entry orders or stops, fee schedules supplied for SOL/BNB with conservative API min-bps floors.
- This is **one instantaneous GET sample**, not cross-checked against multiple independent signed receipts or closed fills; the account-equity-reconciled flag remains false, and no position yet exists on which to verify ISOLATED 10x leverage or broker-hosted 4% stop and position-quantity readback.
- The user-supplied 10x-eligible fee API band result is NOT proof of venue contract minimums or real account position/margin settings.

## Newly implemented

- Explicit **REAL public GET** for `/api/v1/contract/detail/country` and `/api/v1/contract/ticker` on the already verified MEXC API host, no private credentials added to those requests and no exchange write.
- Strict source-verified symbol, contractSize, minVol, volUnit, priceUnit, isolated support, API trading availability, real 10x instrument leverage range, per-country leverage cap, bid1/ask1/fairPrice, and quote age; unknown/missing metadata => fail closed. Contract spec and quote must match same symbol.
- One-minimum-contract margin/risk model at **current MEXC public best ask**, not historical fixed SOL/BNB price. Tick-rounded LONG 4%-below-ask model trigger and pessimistic 2bps slippage per side, taker 8bps per side, hypothetical 5bps funding reserve. Required modeled expected cash-loss <=0.5 USDT per contract. The cap is **not** a guaranteed or broker-verified loss limit; book depth, liquidation/mark trigger, broker-side stop readback, funding settlement and dynamic weakening remain unresolved.
- Integrates public proof into the existing authenticated GET-only `--account-check` diagnostic, prints sanitized specs and whether each one-contract plan meets *model-only* cash risk budget. No LIVE_GO option; no automatic order task.
- New 12 fixed synthetic market stress/failure tests, total **42 tests**, pass on Windows and Ubuntu in CI **38692539591**. Windows packaged EXE requires no operator Python: Actions artifact **11953275092**.
- Current **DRAFT PR #228** remains open; `main` unchanged; no live orders, no MEXC mutations, no credential uploads, no backtest tuning and protected holdout unopened.

## Scientific and operational remaining blockers

1. Exact original causal 5m canonical feed, 1h/4h parity, stale/recency receipts and prospective net-cost sample.
2. Correct **three virtual lanes with at most two independent physical symbols** (SOL_LONG shared+BNB_LONG) with durable account-wide single ownership and crash recovery.
3. Real position-specific native stop placement, exchange acceptance and **later independent state+quantity readback** for fills, partial fills and amendments. MEXC documents asynchronous quantity update for an existing non-final stop at same price. Neither a POST result nor mock test proves protection.
4. No-loss-cap illusions: modeled 0.50 USDT at a stop excludes unbounded gaps, liquidation penalties, execution failures, partial fills and network outages.
5. Signed/idempotent order authority ticket from an independently reviewed risk controller; the current proto-ticket's 64-hex marker must **NOT** be treated as authentic authorization merely because its shape looks valid. No user-initiated auto-arm step is implemented.
6. Full independent current account reconciliation, venue-supported 10x ISOLATED (once position exists), operator final signoff and explicit first-real-trade scoped authority.

**VERDICT: ACCOUNT_READS_PASS_IN_USER_LOCAL_REPORT; REAL_PUBLIC_CONTRACT_GATE_CODE_BUILT_AND_SYNTHETIC_TESTED; ACTUAL_NEW_PUBLIC_SYMBOLS_NOT_YET_OBSERVED; NO_LIVE_GO.**
