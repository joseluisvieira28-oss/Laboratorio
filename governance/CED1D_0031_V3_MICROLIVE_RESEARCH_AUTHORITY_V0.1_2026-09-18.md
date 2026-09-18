# CED1D-0031 — V3 MICRO-LIVE RESEARCH AUTHORITY V0.1 — 2026-09-18

**Branch:** `ced-1d-v3-byte-recovery-2026-09-17`  
**Candidate:** CED1D-0031 — AVAXUSDT Momentum 20D CONTINUATION H1  
**Status:** AUTHORIZED_FOR_ONE_MICROLIVE_RESEARCH_EVENT_FROM_2026-09-21T00:01:00Z  
**Purpose:** collect one real-money execution observation under a tiny, fixed, fail-closed envelope. This is research, not production.

## Scientific identity — unchanged

- Venue/instrument: Binance USD-M perpetual AVAXUSDT
- Signal: 20 calendar-day momentum
- Direction rule: CONTINUATION
- Horizon: H1 = one calendar day
- Signal completion: 00:00:00 UTC
- Reference entry: 00:01:00 UTC
- Reference exit: 00:01:00 UTC one calendar day later
- No stop, target, filter, regime gate, asset substitution, horizon change or post-outcome rescue
- No duplicate signal execution
- Existing CED1D-0031 V3 Tier-2 promotion and prospective-shadow authorities remain controlling scientific parents

## Activation boundary

No micro-live order is eligible before:
`2026-09-21T00:01:00Z`

The eligible trade must come from a signal completed prospectively after the frozen 2026 shadow boundary and emitted on time by the governed radar/collector. Retrospective trade backfill is forbidden.

## Fixed micro-live risk envelope

- Maximum initial notional: **25 USDT equivalent**
- Maximum funded collateral committed to this event: **25 USDT equivalent**
- Maximum simultaneous positions for this authority: **1**
- Maximum real events under V0.1 before mandatory reconciliation: **1**
- Margin mode: **isolated**
- Leverage setting: **1x maximum**
- No pyramiding
- No averaging down/up
- No martingale
- No scaling after a win
- No second real trade until the first event has been fully reconciled and appended to the research evidence chain

## Order model

Entry:
- taker MARKET order only
- execute as close as operationally possible to the frozen 00:01:00 UTC reference
- no order before the signal is final
- no late rescue entry if the governed signal was not available by 00:01:05 UTC
- quantity must be rounded down to venue step size while remaining <=25 USDT equivalent notional

Exit:
- reduce-only taker MARKET order
- target time: exactly 24h after the entry reference, at 00:01:00 UTC next calendar day
- no discretionary early profit-taking
- no discretionary stop-loss
- no extension of the holding period
- if exchange safety/liquidation mechanics forcibly terminate the position, preserve the event as a failure/exception; never rewrite it as a normal exit

## Cost / execution assumptions

Preserve the frozen research floors:
- BASE taker fee floor: 4 bps/fill
- STRESS taker fee floor: 5 bps/fill
- funding: actual signed funding cashflow
- record actual spread/slippage, fills, fees and funding; do not substitute model costs when real receipts exist

Entry fail-closed guard:
- do not enter if observed entry spread + immediate execution slippage cannot reasonably fit inside the frozen STRESS execution envelope
- do not override this guard to “get the trade”

## Mandatory pre-order checks

Every item must PASS:
1. candidate identity exactly CED1D-0031
2. current classification still Tier 2 / Promoted Candidate
3. valid immutable signal key for the current signal day
4. signal completed at or before 00:00:00 UTC and available by 00:01:05 UTC
5. direction exactly matches the frozen CONTINUATION rule
6. public AVAXUSDT USD-M market data fresh and internally consistent
7. no existing AVAXUSDT position or open order for this research authority
8. isolated margin available
9. leverage <=1x
10. notional after rounding <=25 USDT
11. no source/radar/execution health error
12. user remains the final human approver of the real order at the venue

If any item fails: **NO ORDER / FAIL CLOSED**.

## Kill switches

Immediate stop of the micro-live path if any of the following occurs:
- wrong symbol, direction, signal day or signal key
- stale/contradictory market data
- exchange rejects isolated 1x configuration
- order quantity would exceed 25 USDT equivalent
- duplicate order/position detected
- material difference between intended and acknowledged order
- missing fill receipt
- unexpected order type
- inability to verify actual fees or funding after close
- position remains open past the governed exit window without an exchange/system incident record
- any governance file/identity mismatch
- any attempt to scale risk because of the outcome

## Reconciliation required after close

Append and preserve:
- signal key and direction
- intended entry timestamp/reference price
- submitted order timestamp
- exchange order ID copied by the human operator
- every fill timestamp, price and quantity
- actual entry VWAP
- actual exit VWAP
- actual taker fees
- actual signed funding
- actual slippage versus governed reference
- net PnL in USDT and bps
- latency
- any reject/retry/error
- exact evidence receipt hash where available

The historical/shadow evidence must remain untouched. A real loss cannot be discarded and a real win cannot trigger scaling.

## Routing after the first real event

- PASS + clean reconciliation: MICRO_LIVE_EVENT_1_RECONCILED; candidate remains Tier 2 pending further authority/evidence
- negative PnL but clean mechanics: preserve as valid forward evidence; no rescue
- execution/source/governance anomaly: MICRO_LIVE_HALTED pending root-cause review
- no automatic Tier 1
- no automatic second trade
- no production capital

## Explicitly still forbidden

- autonomous order placement by ChatGPT
- account/API credential storage in the repository
- wallets
- transfers/withdrawals
- leverage >1x
- production sizing
- main merge
- strategy tuning
- changing venue/asset to manufacture a trade
- retrospective selection of a “better” Monday signal

## Human execution boundary

ChatGPT currently has no authenticated Binance trading capability in this environment. Binance integration available to ChatGPT is public/read-only and cannot submit transactions. Therefore the governed micro-live order, if eligible, must be reviewed and submitted by the user directly at the venue. This authority defines the exact research envelope; it does not pretend an automated order was placed.

**Current classification remains: TIER 2 — PROMOTED CANDIDATE / QUASE DIAMANTE.**
