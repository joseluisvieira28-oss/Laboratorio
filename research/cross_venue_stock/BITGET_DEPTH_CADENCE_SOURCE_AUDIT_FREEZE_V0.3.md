# BITGET DEPTH CADENCE SOURCE AUDIT V0.3

Date: 2026-10-05
Status: SOURCE-ONLY / POST-VERDICT DIAGNOSTIC

Purpose:
Determine whether the public historical Bitget depth archives can physically satisfy the already-frozen V0.2 execution requirement that a Level1 quote be no more than 5 seconds old for at least 90% of parent signals.

This audit does NOT recompute any strategy signal, fill, return, win/loss or PnL.

Date:
- 2026-09-16 only, the source-verification date already burned before V0.2 outcomes.

Symbols:
- HOODUSDT
- COINUSDT
- ARMUSDT
- AAPLUSDT

For deptType 1 and deptType 2:
- parse snapshot timestamps only;
- measure gap distribution;
- measure neutral every-second quote availability over 14:31–18:44 UTC under the frozen 5s staleness rule.

No execution-model parameter may be changed from this diagnostic.
No private endpoints, account reads, orders, wallets, exchange mutation or live trading.
