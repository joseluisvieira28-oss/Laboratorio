# LIQUIDATION-FLOW-FWD-001 — EXTENDED PUBLIC SOURCE CLOSEOUT V0.13

Date: 2026-10-05
Status: CLOSED AT CURRENT SOURCE GATE

## Authority

Parent branch head before this closeout:
`a29351858748db52c93e4e8dff75be370e77cb07`

Inherited unchanged:
- `V013_PRIORITY_SOURCE_GATE_FREEZE_2026-10-03.md`
- `LIQUIDATION_FLOW_FORWARD_CALIBRATION_FREEZE_V013_V01.md`
- V0.11.6 / V0.12 / V0.12.1 / V0.13 governance and statistical rules.

No MEXC Event Futures outcome was opened for this family.

## Frozen public source

Venue: Bybit public linear websocket
Endpoint: `wss://stream.bybit.com/v5/public/linear`
Topics:
- `allLiquidation.BTCUSDT`
- `allLiquidation.ETHUSDT`

The source gate requires a successful public subscription and at least one valid real liquidation
payload for EACH symbol before source PASS. Missing events are never imputed as zero flow.

## Initial bounded source probe

Run: `37073818293`
Duration: approximately 600 seconds
Verdict: `NO_EVENTS_OBSERVED`
Valid real events:
- BTCUSDT: 0
- ETHUSDT: 0

This was not a no-edge result.

## Frozen one-hour extension

Workflow run: `37075262340`
Job: `111063614589`
Head SHA: `a29351858748db52c93e4e8dff75be370e77cb07`
Run conclusion: `success`
Artifact: `11257963990`
Artifact name: `v013-liquidation-extended-public-source`
GitHub artifact digest:
`sha256:1521ef40603b46a3e76fc148c1e6df9d830faae7c00030ed720e23c45c3e1a5f`

Observed source interval:
- started_at_ms: `1790981904445`
- finished_at_ms: `1790985505432`
- elapsed: approximately 3600 seconds

Transport/source health:
- subscription acknowledgement: PASS
- workflow: PASS
- validator self-test: PASS
- no authenticated or private route used

Valid real liquidation records:
- BTCUSDT: **3**
- ETHUSDT: **0**

The BTC payloads satisfied the frozen schema/freshness checks and preserved raw-message SHA-256
evidence. ETH supplied no valid real liquidation event during the frozen observation window.

## Verdict

`PARTIAL_SOURCE__ACTIVATION_BLOCKED`

Meaning:
- the public source is demonstrated to emit valid timestamped liquidation data for BTC;
- the frozen two-symbol source gate is NOT passed because ETH has no qualifying real event;
- the family is NOT activated;
- no numeric liquidation threshold is calibrated;
- no FOLLOW/Fade result is tested against Event Futures outcomes;
- no edge verdict exists for this family.

This is NOT:
- `SOURCE_GATE_PASS`
- `NO_EDGE`
- `SURVIVES_FORWARD_SHADOW_GATE`

## Consequence

`LIQUIDATION-FLOW-FWD-001` remains outcome-blind and cannot open Event Futures outcomes.

A later continuation is allowed only as a newly committed source-only observation boundary.
If a future public window supplies valid real BTC and ETH events, the next state may become
`SOURCE_PASS_PENDING_CALIBRATION`. The already frozen calibration rule then requires:
- 1440 healthy non-overlapping 60-second UTC bins per symbol;
- at least 100 nonzero valid-event bins per symbol;
- gaps treated as missing, never zero or imputed;
- threshold = frozen nearest-rank 95th percentile of nonzero healthy-bin bankruptcy-price
  notional proxy `sum(v*p)` per symbol;
- no MEXC payouts/index/outcomes during calibration.

Only AFTER calibration may a separate numeric pre-outcome activation freeze be committed.

## Safety / governance

No merge to main.
No login.
No API keys.
No private Event Futures endpoints.
No account/balance/position reads.
No orders.
No wallets.
No spending.
No exchange mutation.
No live trading.
No post-outcome tuning.
No historical Event Futures outcome opened.
