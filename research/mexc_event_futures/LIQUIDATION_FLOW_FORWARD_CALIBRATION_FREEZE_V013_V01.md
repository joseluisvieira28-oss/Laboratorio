# LIQUIDATION-FLOW-FWD-001 — extended source observation and calibration plan

Date: 2026-10-03 Europe/Zurich. SOURCE-ONLY / NO OUTCOMES.
Initial source gate 37073818293: NO_EVENTS_OBSERVED. This is an extension with a new
pre-run boundary, not rewriting or rescuing the frozen 600-second source-gate result.

## Immediate extended probe

Run the identical public Bybit source validator for 3600 seconds, starting only after
this document is committed. Same endpoint, BTCUSDT/ETHUSDT topics, timestamps, raw
hashes, heartbeat and PASS requirements as the priority source gate. No venue pooling.
No hypothetical/synthetic message can count as a real event. Both symbols must provide
at least one valid real event before the source gate passes. If no event arrives, report
NO_EVENTS_OBSERVED; never report failed scientific edge. Gaps terminate this chunk.
The bounded push-triggered run is one explicit research run, not a durable cron.

## Calibration prerequisites

No defensible free historical all-liquidation series has been established in this mission.
Use only future real source data, after a real-message PASS, to calibrate size thresholds.
The extended probe is initial source evidence only, never automatically a completed
24-hour calibration. Preserve raw messages even if transport eventually fails.

Calibration must comprise 1440 healthy, non-overlapping 60-second UTC bins per symbol,
plus at least 100 nonzero valid-event bins per symbol. Extend source-only acquisition up
to seven calendar days if needed; absent/gapped bins are missing, never zero or imputed.
Resume requires a continuity receipt with earlier raw manifests, gap list and boundaries.
Do not claim an empty minute as healthy solely from the absence of data; require public
acknowledgement + heartbeat health and a healthy no-gap connection across that minute.
Calibration must not subscribe to MEXC index, payouts, returns, candles or outcome labels.

Within a healthy bin, notional proxy = sum(v*p) using bankruptcy price p, explicitly not
a true executed notional. Side Buy means long liquidated -> forced selling; Sell means
short liquidated -> forced buying. Preserve all events, including identical array items.
The numeric threshold per symbol will be the nearest-rank 95th percentile of nonzero
healthy-bin total notional proxies, with rank ceil(.95*n). Persist bins and exact source
hashes. No price/return-based threshold selection, no alternative quantile search.

## Predeclared activation template, currently NOT ACTIVE

After calibration, commit a separate pre-outcome activation freeze with the actual two
numeric thresholds, calibration receipt/hash and a new future boundary. Until then,
registry stays SOURCE_GATE_REQUIRED or SOURCE_PASS_PENDING_CALIBRATION.

Direction policy is fixed now as FOLLOW_FORCED_FLOW, never FADE chosen from outcomes:
- sell pressure from long liquidations > buy pressure: DOWN;
- buy pressure from short liquidations > sell pressure: UP;
- exact equality: NO_SIGNAL.
Signal requires total proxy >= symbol threshold AND absolute signed imbalance / total
>=0.80. Use one finalized healthy 60-second bin; horizon exactly 10 minutes; max source
signal age 5 seconds; first-only unresolved overlap; min N=100 per symbol; exact V0.13
payout/index/expiry/statistics unchanged. Last valid event time is the signal source time;
stale-last-event bins cannot be rescued using their bin closing clock.
Rule hash must include the eventual numeric thresholds and source calibration hashes.
No MEXC outcomes open until that fully populated numeric activation freeze is committed.

## Safety and stopping

No login, credentials, private endpoints, account reads, wallets, orders or live trading.
No main change, no paid source. The 3600-second extended run may yield another source
verdict; it cannot yield a trading edge or a calibrated/activated family by itself.
