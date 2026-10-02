# TRIPLE FISHING MULTI-SLOT V0.4 — PRE-LIVE ENGINEERING FREEZE

Date: 2026-10-02

## Objective

Implement the user's requested **minimum three-slot** operator architecture without weakening the scientific identities of OPTIONS, BNB, or DH03.

This freeze is intentionally aggressive on capacity and conservative on absolute exposure.

## Frozen capacity target

- maximum simultaneous positions: **3**
- one active position per symbol: **required**
- late chase: **forbidden**
- blind resend: **forbidden**
- isolated margin only
- Auto Margin Add OFF
- no martingale / averaging / pyramiding

## Small-fish risk envelope

Global:
- maximum aggregate notional: **30 USDT**
- maximum aggregate initial isolated margin: **14 USDT**
- daily realized-loss kill: **5 USDT**
- rolling 7-day realized-loss kill: **5 USDT**

Per lane:
- OPTIONS: **1x**, max **10 USDT notional**, max one active position
- BNB: **5x**, max **10 USDT notional / 2 USDT initial margin**, max one active position
- DH03: **5x**, max **10 USDT notional / 2 USDT initial margin**, up to three DH03 positions subject to the global cap and one-per-symbol rule

If the venue minimum exceeds a lane's 10 USDT notional cap, the signal is **blocked**. The operator must never enlarge size merely to satisfy venue minimums.

## Why this is separate from V0.3

V0.3 is structurally one-slot:
- one account-wide reservation;
- one active state manager;
- risk state blocks at one effective open position;
- generic 5x envelope conflicts with the separately frozen 1x OPTIONS execution fork.

V0.4 must therefore be a real architecture change, not a constant edit.

## Mandatory engineering gates before any live activation

1. durable capacity-3 reservation ledger;
2. deterministic capacity-aware no-chase arbitration;
3. portfolio aggregate risk firewall;
4. lane-specific leverage/sizing validation;
5. multi-active-position lifecycle;
6. restart / unknown-ack / reconciliation fault injection;
7. independent exit ownership;
8. authority/manifest/runtime reconciliation;
9. fresh authenticated read-only exchange feasibility;
10. Windows build + readiness;
11. explicit V0.4 live authority.

## Governance

This freeze authorizes engineering and validation on the branch only.

It does **not**:
- arm V0.4;
- create an exchange order;
- modify the account;
- merge main;
- supersede the current V0.3 live authority.
