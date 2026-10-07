# MEXC GLOBAL-ASSET INTRADAY OVERSHOOT — V0.2.4 TRANSPORT REMEDIATION CLOSEOUT

Date: 2026-10-07
Branch: `mexc-globalasset-intraday-overshoot-shadow-v0.2.4-ws-remediation-2026-10-07`

## Authority

Scientific authority remains unchanged:
- `MEXC_GLOBALASSET_INTRADAY_OVERSHOOT_SHADOW_FREEZE_V0.2.md`
- amendments V0.2.1–V0.2.4

Historical family remains:
`ROBUST_API_FEE_SURVIVOR`

V0.2.4 is a clean prospective epoch and does not pool V0.2.3 receipts.

## Frozen transport remediation

Signal K-line transport is now:
- Binance: existing official public USD-M market WebSocket
- MEXC: public contract WebSocket `wss://contract.mexc.com/edge`, `sub.kline`, `Min1`
- Bitget: public v3 WebSocket `wss://ws.bitget.com/v3/ws/public`, `kline`, `1m`

MEXC REST remains only for startup contract metadata and trigger-time entry/exit public depth.

## Outcome-blind evidence

Transport probe workflow:
- run: `37635584092`
- conclusion: SUCCESS
- MEXC: 35 subscriptions sent; `push.kline` observed; public ping/pong observed
- Bitget v3: 35 subscriptions sent; K-line data observed with expected schema
- economic outcomes scored: FALSE

Self-test workflow:
- run: `37636132540`
- conclusion: SUCCESS
- 35/35 MEXC bindings constructed
- 35/35 Bitget bindings constructed
- 35/35 Binance bindings constructed
- frozen 5m / 10bps / 40bps / 35bps invariants verified
- closed-minute mapping: PASS
- same-contract fill invariant: PASS
- empty V0.2.4 epoch: `EXECUTION_SHADOW_UNDERPOWERED`
- live public transport proof: PASS

## Capture

Capture workflow:
`.github/workflows/mexc-globalasset-intraday-overshoot-v024.yml`

Trigger namespace:
`research/mexc_global_assets/shadow_trigger_v024/**`

The first valid V0.2.4 economic session must begin strictly after the V0.2.4 freeze commit timestamp:
`2026-10-07T14:16:49Z`.

No 2026-10-07 V0.2.4 session is valid because the frozen scan session had already started before the amendment boundary.

First eligible session:
`2026-10-08`.

## Current verdict

`EXECUTION_SHADOW_UNDERPOWERED`

Operational sub-status:
`V0.2.4_CAPTURE_READY`

Reason:
transport and runtime tests pass, but zero V0.2.4 economic event baskets and zero V0.2.4 session dates exist yet.

Frozen final gate remains:
- >=30 admitted event baskets
- >=5 distinct session dates
- measured executable book economics after 16 bps fees positive under all frozen PASS criteria

No orders, private endpoints, account reads, wallets, exchange mutation, live trading, main merge, backfill or post-outcome tuning.
