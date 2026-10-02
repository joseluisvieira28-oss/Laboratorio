# V0.13 priority family source gates — pre-run freeze

Date: 2026-10-03 (Europe/Zurich). SOURCE-ONLY / OUTCOME-BLIND.
Parent: 196e5df3ba50de84e03c91faeccf0e6df7db4f29.
Inherits V0.11.6, V0.12, V0.12.1 and EVENT_CONDITIONED_EDGE_FREEZE_V0.13.md unchanged.

## No outcomes or activation

These probes do not subscribe to MEXC prices, collect payouts, compute returns,
read prior research outcomes, activate families or change the frozen registry.
No login, credentials, private endpoints, account reads, wallets, orders or spending.
Only public market-data GET and public websocket subscribe/ping are allowed.
Raw response bytes/messages, receive times and SHA256 are preserved.
Failures and rejected observations are preserved; documentation/examples never count as live evidence.

## LIQUIDATION-FLOW-FWD-001

Source: wss://stream.bybit.com/v5/public/linear.
Topics: allLiquidation.BTCUSDT and allLiquidation.ETHUSDT.
Official specification: https://bybit-exchange.github.io/docs/v5/websocket/public/all-liquidation
Connection: https://bybit-exchange.github.io/docs/v5/ws/connect
Probe duration: 600 seconds, with public heartbeat every 20 seconds.
No alternate venue is silently pooled with Bybit.

Require successful subscription acknowledgement and at least one valid real liquidation
for each symbol: source T and envelope ts integer milliseconds, positive finite v and p,
S exactly Buy or Sell, correct symbol/topic, local receive minus T in [-1000,5000] ms,
and T no more than 1000 ms after envelope ts. Preserve receive clock and all source clocks.
Buy means a LONG position liquidated (forced selling); Sell means SHORT liquidated
(forced buying). p is BANKRUPTCY price, not a demonstrated fill price. v*p is only a
bankruptcy-price notional proxy; no claim of true executed USD notional.
Bybit documentation claims all liquidations on this venue; this probe cannot independently
prove completeness across outages or all exchanges. Missing events never become zero flow.
No exchange event ID is supplied; raw envelope hash + array ordinal is evidence identity.
Do not collapse identical array items merely because economics/timestamps coincide.

Verdicts: SOURCE_GATE_PASS (both symbols), PARTIAL_SOURCE (one),
NO_EVENTS_OBSERVED (acknowledged but no valid events), SOURCE_BLOCKED (transport/schema).
Zero events is not a no-edge verdict. Connection gaps invalidate affected calibration bins.
If no defensible free historical source is proven, use a separate forward source-only
calibration period before freezing numeric flow thresholds, without Event Futures outcomes.

## OPTIONS-VOL-FWD-001

Source: https://www.deribit.com/api/v2/public/ (production, unauthenticated GET).
Allowlist: get_instruments, get_book_summary_by_currency, ticker.
Official ticker: https://docs.deribit.com/api-reference/market-data/public-ticker
Currencies: BTC, ETH; inverse options only; nearest active expiry in [7,30] days.
Instrument metadata proves option type, expiry and strike. Summary data selects two
OTM candidates per side closest to an approximate 25-delta strike, using current forward,
mark IV and time to expiry. This approximation is only query selection, never the signal.
Actual ticker greeks.delta must be in [0.15,0.35] for calls, [-0.35,-0.15] for puts.
Select by closest actual delta to +/-0.25, then instrument name. No interpolation.
Three independent request rounds, separated by 10 seconds, must each yield a matched
call/put pair for both currencies and the same expiry selected in that round.
Pair maximum source timestamp spread 5000ms. Ticker age on receive in [-1000,5000]ms.
Positive finite mark_iv, bid_iv, ask_iv, index_price, underlying_price, best_bid_price,
best_ask_price and bid/ask amounts; ask >= bid; bid_iv <= ask_iv; state open;
finite actual delta; response/instrument identity exact. Missing/zero/nonfinite values reject.
Raw JSON and metadata hashes link every accepted pair. HTTP success alone is insufficient.
IV is quoted in percentage points, not a probability or a directional forecast.

Verdicts: SOURCE_GATE_PASS (3/3 pairs for BTC and ETH), PARTIAL_SOURCE,
SOURCE_BLOCKED. Skew is prospective put mark IV minus call mark IV; it has not yet been
validated as a predictive edge. Never reuse invalid/stale IV from earlier labs.

## Next boundary

For a PASS, commit a family-specific pre-outcome activation freeze with immutable
direction, horizon, freshness, overlap, minimum N, rule hash and forward boundary
before any outcome collection. If calibration is necessary, freeze its source-only
procedure and keep activation PENDING_CALIBRATION until numerical thresholds are committed.
The strongest possible later promotion remains SURVIVES_FORWARD_SHADOW_GATE.

## Execution

Local probes and bounded push-triggered GitHub Actions are permitted research runs.
No branch-only cron is presented as a durable collector. No main change/merge.
Evidence artifacts are uploaded even when a source gate fails; each manifest hashes raw files.
