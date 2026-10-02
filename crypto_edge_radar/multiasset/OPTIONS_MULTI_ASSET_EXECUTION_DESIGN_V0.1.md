# OPTIONS MULTI-ASSET — EXECUTION DESIGN V0.1

Status: DESIGN ONLY / NO LIVE AUTHORITY

## One rod, four hooks

A single supervisor can own four independent OPTIONS observation lanes:

- OPTIONS-BTC-001
- OPTIONS-ETH-001
- OPTIONS-SOL-001
- OPTIONS-XRP-001

Each lane can emit only its own asset and its own immutable signal identity.

## Futures-only mapping

| Hook | Positive signal | Negative signal |
| --- | --- | --- |
| BTC | LONG BTC_USDT | SHORT BTC_USDT |
| ETH | LONG ETH_USDT | SHORT ETH_USDT |
| SOL | LONG SOL_USDT | SHORT SOL_USDT |
| XRP | LONG XRP_USDT | SHORT XRP_USDT |

Spot is not part of the target execution architecture.

## Shared risk firewall

Initial design:
- one real-money slot across all four hooks;
- isolated margin;
- fixed authority-defined leverage;
- no auto-add margin;
- no martingale;
- no averaging;
- candidate-specific immutable order identity;
- no blind resend after ambiguous acknowledgement;
- fresh contract/fee/funding/account preflight;
- venue minimum must fit inside the frozen candidate cap;
- deterministic arbitration if two hooks become executable simultaneously.

Shadow/forward evidence for all hooks continues even when the real-money slot is occupied.

## Important separation

The supervisor may share:
- scheduling;
- source-health framework;
- evidence store;
- execution transport;
- risk firewall;
- reconciliation;
- telemetry.

It must NOT share:
- scientific result;
- promotion status;
- protected outcomes;
- candidate-specific thresholds unless frozen independently;
- execution authority.

## Promotion to live-capable hook

For ETH/SOL/XRP, the execution route remains disabled until all of the following exist:

1. Source/Data Gate PASS.
2. Pre-outcome science freeze committed.
3. Development result meeting its frozen gates.
4. Independent OOS/holdout result if required.
5. Prospective forward evidence gate.
6. MEXC execution-feasibility gate.
7. Candidate-specific live authority.
8. Supervisor registry update explicitly enabling that hook.

This document alone authorizes none of those steps.
