# BTC-OPTIONS-VRP-001 V2 — 30D HOLD-TO-EXPIRY SOURCE CLOSEOUT V0.1
Date: 2026-10-07
Status: SOURCE-ONLY

Freeze: USDC_30D_EXPIRY_SOURCE_GATE_FREEZE_V0.1.md
Workflow run: 37663564452
Artifact: 11502211371
Artifact digest: sha256:7571cee3541733fc39a1909a5e55e5e389604c3d0caf32e4c348446bc8e3b867

## Result
- 52 frozen 2025 Thursday anchors examined;
- exact qualifying same-strike 25–35 DTE call+put entry pairs with direction=SELL on both legs: 0;
- required source-feasibility floor: 24;
- prices retained: false;
- settlement values opened: false;
- returns/PnL computed: false.

Canonical classification:
**SOURCE_ENTRY_INSUFFICIENT**

This source verdict applies only to the aggressive-seller trade-print entry proxy. It is not NO_EDGE and does not adjudicate the VRP economic mechanism.

A distinct source-only liquidity-witness probe may inspect whether real trades exist on both legs regardless of aggressor direction. Such a probe may establish market activity but cannot by itself prove that a passive seller would receive a fill.
