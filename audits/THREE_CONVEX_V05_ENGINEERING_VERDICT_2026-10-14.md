# CRYPTO LAB — THREE CONVEX V05 ENGINEERING CLOSEOUT (2026-10-14 UTC)

## Purpose and operator request

Operator requested maximum autonomous work toward an unattended MEXC Futures 100 USDT / 10× ISOLATED multi-slot bot using ORIGINAL SOL native5m, SOL1h, BNB4h CONVEX V5, no half-profit redesign. Previous standing boundaries: no main merge, wallet or authenticated read/write or live order, no 2026 sealed holdout, no post-outcome tuning. Operator reported HEDGE in MEXC UI, 100 USDT, zero positions; account status NOT independently authenticated. On Windows three legacy trading Scheduled Tasks all Disabled; watcher Ready; matching legacy executable name search returned zero rows. These observations do not prove no open brokerage positions/orders.

## Actual GitHub changes

- Draft PR **#227** branch `engine/three-convex-v05-shadow-core-2026-10-14` against PR #226's prelive branch; **no main merge**.
- Byte-for-byte pinned Git blob `19c8b8e2363f253458db42111b6701f3a3ef1f4b` from historical V5 source; AST only extracts original SMA, stdev, Wilder RSI and build_signals. On Windows normalize CRLF only to calculate the canonical Git blob identity. 1h/4h TF derived from consecutive 5m, not independent vendor 1h.
- `signals.py`: validated candle source, true 5m align/continuity, only completed TF bars, strict 5m delay to entry from completed signal.
- `shadow.py`: deterministic interleaved SOL/BNB shadow engine; original V5 4% initial stop, *NONLATCHED* 12% trailing at +5% completed own TF, gap first, stop before trailing update. Logs weakening rather than pretending monotonic safety. No pretense the stop is actual broker-hosted.
- 1 minimum physical contract model from user-reported 14 Oct MEXC public query: 0.1 SOL / 0.01 BNB, isolated 10x, modeled cash risk<=.50 USDT per slot, aggregated<=1.50, SOL<=1.00, account declared 100 USDT. 8bps fee/side, 2bps adverse slippage/side, single 5bps assumed funding debit. These are NOT authenticated MEXC fees or fill models. Input is labeled Binance canonical 5m; no source custody verification or actual MEXC bid-ask matching.
- Same-side SOL signals collide under HEDGE. The second SOL reservation when first exists is blocked. If two SOL signals coincide on same completed bar, BOTH rejected, not arbitrarily advantaging one.
- `run_offline.py`: pure file source-asserted JSONL or synthetic QA, immutable output directory, hash-chain shadow receipts, signal/event evidence. Original science 2023–25 and locked 2026 outcomes not opened in CI.
- `broker_protocol.py`: future read-only account structural gate (HEDGE/ISOLATED 10x, no un-reconciled positions/orders, current fee and margin tier); order/position/protective stop structural identity+quantity+4%+trigger+timing gate; durable first-write-wins idempotent intent, no blind resend upon crash/unknown state. **No authenticated broker API or order transport.** Mock tests are only structural, not evidence of account or broker acceptance.
- Windows and Ubuntu CI workflow, 1-level Windows Actions artifact incl QA launcher; excludes secrets, no order or authenticated account API.

## Measured QA

- Windows + Ubuntu CI latest PASS on run **38625105691**, commit `eaba28c89663f1fec83198b74c94f0803b792d66`.
- **49/49 offline/synthetic unit tests** passed on Windows and Ubuntu; original source Git blob match, forced gaps/timeframes, simultaneous SOL, dual SOL+BNB model, stop gap exposure worse than 0.50 modeled-risk, weakening original trail recorded, no broker methods, immutable evidence rejection, mock position/stop account and restart uncertainty gates.
- Synthetic report always `OFFLINE_SHADOW_ENGINE_COMPLETE_NO_LIVE_GO`, execution_authority `NONE`, broker_transport_present false, realized_live_trade_count 0. Windows artifact `11923512041` named `Three_CONVEX_V05_SHADOW_NO_LIVE_GO`. Source pin and 49 tests are engineering evidence ONLY, not forward alpha or live execution security.

## Official current MEXC contract API semantic warning (external documentation, NOT tested against account)

- `https://www.mexc.co/api-docs/futures/account-and-trading-endpoints/place-plan-order` describes `POST /api/v1/private/planorder/place/v2`, can attach `stopLossPrice` to a trigger **plan order**; does not itself prove that a normal entry is instantly covered at the MEXC engine or returns an appropriate broker-side position stop ACK.
- `https://www.mexc.co/api-docs/futures/account-and-trading-endpoints/place-tpsl-order-by-position` describes `POST /api/v1/private/stoporder/place` requiring position ID and stop price. Critically warns: an existing unfinished TP/SL at the same price can return its previous ID and **adjust quantity asynchronously**. Therefore an API success response is **NOT sufficient**: separate authenticated fresh stop-list reread must confirm exact filled position ID, quantity and trigger state. Never build trading authority from synthetic ack tests.
- `https://www.mexc.co/api-docs/futures/account-and-trading-endpoints/get-order-information-by-order-id` reports `positionId`, filled volume, attached `stopLossPrice`, `positionMode` and exact trade info; read-only cross-validation is possible only once a real permission-scoped adapter exists.
- Old actual MEXC operator V03 [PR #165] was exactly 5x/one-global-slot for different strategies and explicitly states installing an unarmed supervisor can nevertheless manage existing position. Do **NOT** re-enable or reuse for these three lanes directly.

## Legitimate verdict: NO LIVE GO

**V05 OFFLINE SHADOW CORE: BUILT AND CROSS-PLATFORM TESTED. V05 UNATTENDED REAL-MONEY BROKER EXECUTOR: NOT BUILT, NOT VALIDATED, NOT ARMED. There is no hidden GO switch.**

Fail-closed blockers (not a relabeling of passed offline tests):
1. Verified continuous timestamped live original **Binance 5m source** and external signal parity on 5m/1h/4h without contaminating protected 2026 holdout. Full-period historical RSI warmup and network cadence must match parent. Standalone user-asserted data file is NOT custody.
2. Independently **authenticated read-only** *current* MEXC Futures equity, open positions and pending orders and TP/SL, fee schedule, margin/leverage account tier, price tick, min notional, funding/mark-liquidation buffer; account data from 21 Sep 2026 is stale.
3. A separately reviewed **MEXC auto-executor** for three original strategy signals, protection with exchange-hosted stop matching each actual fill quantity, dynamic stop change including original NONLATCHED weakening semantics, idempotency and reconnect reconciliation, scope/risk authority and safety after PC/exchange outage. Current mock adapter cannot submit or protect real money.
4. **New, prospective, venue- and sizing-specific, costed shadow evidence after freeze** sufficient to warrant economic deployment; historical 2023–25 return +59.9%/+59.4%/+27.4% is NOT independent 2026 OOS and 1-contract sizing is not original 20%-notional policy.
5. Explicit approved final candidate-specific live authority and user final signoff after all evidence. Never force a trade merely to validate connectivity; no blank or fake stop ACK accepted.

No order, account read, spending, trade, authenticated API, altered historical closeout, wallet, or main merge in this work. Preserve old task Disabled, no need for user to rerun previous PRELIVE checks.

**Next engineering execution sequence:** implement strictly read-only fresh account/broker observer under user's existing Windows DPAPI WITHOUT exposing secrets, ingest public 5m source with closure/custody stamps, validate longitudinal forward signal parity, design/mock exact broker stop read-after-write and crash replay, independently verify feasibility/alpha. A real broker adapter must be reviewed separately and can only be armed after all gates + deliberate signoff. No background tasks promised by this document.
