# MEXC Tier-2 Micro-Live V0.3 — OPTIONS V2.1 SHORT lane

Status: **PRE-LIVE PACKAGE / FAIL-CLOSED / NO ACTIVE AUTHORITY INCLUDED**

## What changed

This package implements the frozen `TIER2-MICROLIVE-POLICY-V1.0-FROZEN-2026-09-24` execution envelope:

- maximum live notional: **10 USDT**;
- leverage: **exactly 1x**;
- Futures margin: **ISOLATED**;
- maximum concurrent micro-live positions: **1**;
- daily realized-loss kill: **2 USDT**;
- rolling 7-day realized-loss kill: **5 USDT**;
- no martingale, averaging-down or automatic size escalation.

The old ETF-specific 0.1% equity allocation is NOT used by the V0.3 Tier-2 gate.

## First executable lane

`OPTIONS-SPOTPERP-001-V2.1` — **negative canonical signal only**.

Frozen scientific identity:
- signal: CALL_IV_MINUS_PUT_IV;
- negative = SHORT;
- entry: 00:00 UTC t+1;
- exit: 00:00 UTC t+2;
- leverage above 1x forbidden;
- STRESS cost budget: 20 bps full notional.

Execution translation:
- negative signal -> MEXC `BTC_USDT` perpetual SHORT;
- maximum post-midnight execution latency: **30 seconds**;
- observed canonical runtime on 2026-09-25 materialized the prior-day signal by 00:00:10.527 UTC;
- this latency allowance is execution-feasibility only and does not rewrite the historical 00:00 scientific entry;
- isolated 1x;
- Auto Margin Add OFF;
- max 10 USDT notional;
- this translation produces execution evidence only and receives **zero automatic scientific promotion credit**.

A LONG OPTIONS signal is never silently converted to a SHORT. It is NO_TRADE on this V0.3 lane until a separately frozen Spot-long route exists.

## Required sequence before any real order

1. Upgrade Radar Windows separately to V0.14.4 / registry 3.7 / 8-of-8.
2. Run `Run_MEXC_Tier2_Ready_Check_V03.ps1` (read-only).
3. Require global authenticated preflight PASS.
4. Require current venue minimum <= 10 USDT.
5. Require Tier2 risk-state PASS.
6. Require a genuinely current canonical OPTIONS V2.1 SHORT signal.
7. Create a candidate-specific immutable authority from the V0.3 template.
8. Run executor **without --execute** first; it must return `TRADE_READY_NOT_SUBMITTED`.
9. Only a later explicit activation step may set the local execution token and invoke `--execute`.

## Hard fail-closed conditions

- stale/missing preflight;
- stale/missing risk state;
- LONG/FLAT/invalid signal;
- source unhealthy;
- Radar motor unhealthy;
- wrong signal identity;
- venue minimum > 10 USDT;
- requested notional > 10 USDT;
- daily loss >= 2 USDT;
- rolling 7-day loss >= 5 USDT;
- any existing micro-live position;
- any open Futures order/position at last-moment reconciliation;
- leverage not exactly 1x;
- margin not isolated;
- Auto Margin Add OFF not verifiable;
- kill switch present;
- duplicate signal/intent;
- missed entry window;
- wrong 24h exit target;
- missing/incorrect live execution token.

No active candidate authority and no API secret are included in the artifact.
