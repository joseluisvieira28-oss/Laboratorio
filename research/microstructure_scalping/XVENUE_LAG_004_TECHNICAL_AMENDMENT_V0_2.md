# XVENUE-LAG-004 — TECHNICAL SOURCE AMENDMENT V0.2

Date: 2026-09-26
Status: TECHNICAL ONLY — SCIENCE UNCHANGED

The first forward run was BLOCKED before evaluation because incremental MEXC depth was initialized from a REST snapshot before the WebSocket subscription, creating a version discontinuity.

No scientific outcome was opened.

Technical correction:
- use documented MEXC public `sub.depth.step` channel;
- consume `bidMarketLevelPrice` and `askMarketLevelPrice` directly;
- retain version monotonicity as a diagnostic;
- version skips no longer imply a corrupted BBO because no local incremental book is reconstructed;
- non-monotonic versions still fail closed.

Unchanged:
- 180s capture;
- 60s feature-only calibration;
- 120s evaluation;
- 50ms receive-time grid;
- Binance/Bybit leaders;
- 100/250ms leader windows;
- p95/p99 thresholds;
- lag condition;
- future horizons;
- 12/16 bps MEXC fee hurdles;
- survival rule.
