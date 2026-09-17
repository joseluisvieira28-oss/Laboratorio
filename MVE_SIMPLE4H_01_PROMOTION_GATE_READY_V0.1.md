# MVE-SIMPLE4H-01 — PROMOTION GATE READY — V0.1

Date: 2026-09-17
Branch: simple4h-recovery-v0.2
Status: PROMOTION_GATE_READY / PROTECTED OUTCOMES NOT OPENED BY THIS FILE

## Authority recovered
The original SIMPLE_TRADING_LAB_V0.1 package, scientific freeze, 36-cell summary, event ledger and closeout were recovered. The prior SOURCE_RULE_RECOVERY_BLOCKED state is therefore superseded for the new MVE replication family only. Historical verdicts remain immutable.

## Frozen family
Seven fixed 4H diagnostics, selected by the pre-existing MVE authority before protected outcomes:
- ST-01 Donchian Breakout: BNBUSDT, DOGEUSDT, SOLUSDT, XRPUSDT
- ST-02 EMA Pullback: SOLUSDT, DOGEUSDT
- ST-03 Extreme Mean Reversion: DOGEUSDT

No member may be removed or added after protected outcomes are opened.

## Recovered execution geometry
- Timeframe: 4H
- Entry: next-bar open after signal
- ATR: 14
- Donchian: 20-bar breakout; stop 2 ATR; target 4R; timeout 20 bars
- EMA Pullback: EMA20/EMA50; stop 1.5 ATR; target 2R; timeout 10 bars
- Extreme Mean Reversion: EMA20 +/- 2 ATR; stop 1.5 ATR; target frozen EMA20; timeout 8 bars
- Base round-trip cost: 10 bps
- Stress round-trip cost: 14 bps
- Same-bar stop/target ambiguity: adverse/stop-first
- Discovery authority: 2021-01-01 through 2024-12-31
- Protected periods remain separate; this document does not authorize 2026 access.

## Historical evidence only — not promotion evidence
The recovered seven cells contain 2,332 Discovery trades in aggregate. All seven had positive mean net expectancy at both 10 bps and 14 bps, but none passed the original strategy-family BH-FDR gate. Historical drawdowns were large. These facts justify replication only; they do not constitute OOS evidence or promotion.

## Contamination firewall
- 2021-2024: exposed/contaminated by original Discovery; may be used only for code parity and historical reproduction.
- 2025: protected candidate evaluation period. Do not inspect outcomes until the one-shot protocol and source audit are frozen.
- 2026+: LOCKED. No access authorized by this gate.
- No tuning, threshold changes, cost changes, asset selection, strategy selection or survivor selection after 2025 outcomes.

## One-shot 2025 protocol to arm
Target window: 2025-01-01T00:00:00Z inclusive to 2026-01-01T00:00:00Z exclusive, subject to source completeness and timestamp contract.

Source requirement: authoritative reproducible 4H OHLCV for all required Binance Spot symbols, with source receipts/hashes and complete-month audit before outcomes are computed. Fail closed on missing/duplicate bars, unresolved timestamp semantics, symbol-history incompatibility or incomplete source provenance.

Run all seven frozen cells in one invocation. Produce immutable event ledger, per-cell summary, family summary, source manifest, code hash and closeout.

## Frozen evaluation outputs
Per cell:
- N
- gross mean bps
- net mean bps @10 and @14
- median net bps
- win rate
- standard deviation / standard error
- 95% CI
- one-sided p-value for mean > 0
- BH-FDR q-value within the pre-frozen seven-cell family
- profit factor @10 and @14 where computable from event returns
- max drawdown
- mean R multiple
- stop/target/time-exit rates
- monthly/quarterly stability diagnostics
- bootstrap lower 95% bound using frozen block-bootstrap semantics

Family-level outputs:
- equal-weight seven-cell expectancy @10 and @14
- family PF @10 and @14
- number of positive cells @10 and @14
- concentration share of aggregate PnL by strongest cell
- strategy and asset concentration diagnostics

## Adjudication ladder
This MVE uses the pre-existing MVE principle: lower the requirement for perfection, never waive negative economics.

MVE-2 / OOS_POSITIVE requires at minimum:
1. frozen family equal-weight net expectancy > 0 at 10 bps;
2. frozen family equal-weight net expectancy > 0 at 14 bps;
3. family PF > 1 at 10 bps;
4. no source/provenance failure;
5. no post-outcome modification of the seven-cell family;
6. result not wholly dependent on one accidental subgroup without disclosure.

Cell-level p/q values are diagnostics and multiplicity controls; no single cell may be cherry-picked to rescue a failing family. A stronger promotion beyond MVE-2 requires additional independent evidence under the canonical Near-Diamonds governance.

Immediate fail/stop conditions:
- family net expectancy <= 0 at base cost;
- family PF <= 1 at base cost;
- source/provenance failure;
- execution mismatch versus recovered authority;
- post-outcome rule or family mutation.

Stress-cost failure with base-cost pass is retained as fragile evidence and cannot be called robust OOS positive under this freeze.

## Current decision
PROMOTION_GATE_READY.
No 2025 outcomes were opened or computed in creating this gate. 2026 remains locked.
Next lawful action: source-only 2025 coverage/provenance audit, code-parity tests against exposed 2021-2024 authority, then one-shot 2025 execution only after those gates pass.