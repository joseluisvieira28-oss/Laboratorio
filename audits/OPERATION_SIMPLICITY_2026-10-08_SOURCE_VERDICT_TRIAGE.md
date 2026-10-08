# CRYPTO LAB — OPERAÇÃO SIMPLICIDADE — AUDITORIA SEM NOVAS MINAS
Date: 2026-10-08
Scope: read-only source and verdict audit of existing repo branches, performed from ChatGPT GitHub connector.
Authority: user requested focus on SIMPLE, low-turnover automated trading with real after-cost edge; no new strategy creation, no trades, no protected outcome opening, no post-outcome tuning, no main merge.
This document is a navigation/triage audit, NOT a new scientific freeze, backtest, forward result or promotion.

## Canonical closeout evidence and scientific state

1) TFG-DONCHIAN-1D-001 MEXC spot: 2025 OOS 40 resolved trades, +0.3510844126 net R/trade, PF 1.5851406877, BASE 0.20% and STRESS 0.30% round trip. 2025 bootstrap CI [-0.4273483181,+1.1005416049] and 2025-Q3 profit concentration. The same exact rule in protected 2026 Jan-Aug: 30 trades, -0.5078522823 R/trade, PF 0.3905772612, STAGE_A_2026_PROTECTED_FAIL / STOP_NO_RESCUE. Do not present 2025 OOS survival as current executable edge.
2025 source: branch tfg-donchian-1d-oos-2025-v01, `Dream-Account-OS-v2.3-PARTIAL/research/timeframe_gap/TFG_DONCHIAN_1D_001_2025_OOS_CLOSEOUT_V0.1D.md`
2026 source: same branch, `Dream-Account-OS-v2.3-PARTIAL/research/timeframe_gap/TFG_DONCHIAN_1D_RAPID_VALIDATION_V0.2_STAGE_A_2026_CLOSEOUT.json`

2) TFG-DONCHIAN-INTRADAY 12H,8H,4H: all positive W1/W2 but all negative W3 Jan-Aug 2026: D12 -0.533511 R PF .377571; D8 -0.614527 R PF .297675; D4 -0.387946 R PF .532475. Fine scales 3H,2H,1H also negative W3. `COMPLETE_NO_CELL_PASSES_ALL_WINDOWS`; DO NOT rescue through alternate timeframe.
Sources: same branch, `.../TFG_DONCHIAN_INTRADAY_FAMILY_12H_8H_4H_CLOSEOUT_V0.1.json` and `.../TFG_DONCHIAN_FINE_SCALE_3H_2H_1H_CLOSEOUT_V0.1.json`.

3) TFG-DONCHIAN-REGIME-ADAPTATION-V1: frozen pre-outcome market-wide bull participation filter (BTC fully closed UTC daily > SMA200; SMA200 rising vs 20 complete days prior; >=4/6 assets > own SMA100). D12 12H LONG-only, stop signal low - 0.25*ATR28, target 3R, 80-bar max hold, base 0.20%, stress 0.30%. 2025 filtered 50 trades, +0.405404475 R, PF 1.653878; 2026 unfiltered -18.67286868 total R and filtered zero trades because gate was OFF; 2026 is explicitly CONTAMINATED DIAGNOSTIC ONLY, NOT INDEPENDENT EDGE CONFIRMATION. The prospectively frozen forward is required. Existing watcher state from Sep24: 0 evaluated 12H closes, 0 resolved, 3 public MEXC source failures; `ACTIVE_PAPER_SHADOW_SOURCE_FAILURE_FAIL_CLOSED`. Its existing API binding is public unauthenticated GET api.mexc.com/api/v3/klines; no source substitution/backfill. The branch file is the last persistent state read; it may not reflect later out-of-repo runtime activity. DO NOT claim current live health from this file alone.
Sources: same branch `.../TFG_DONCHIAN_REGIME_ADAPTATION_V1_CLOSEOUT.json`, `.../TFG_DONCHIAN_REGIME_ADAPTATION_V1_FORWARD_FREEZE.json`, `.../TFG_DONCHIAN_REGIME_ADAPTATION_V1_FORWARD_WATCH_STATE.json`, `.../TFG_DONCHIAN_REGIME_ADAPTATION_V1_FORWARD_WATCHER_SPEC.json`.

4) SIMPLE TRADING LAB/MVE-SIMPLE4H-01 independent 2025 seven-cell 4H replication: 633 trade ledger, 7/7 adequate cells, just 1/7 OOS positive (XRP Donchian, no strong evidence), 0/7 strong, 5/7 negative net14, family median NET14 -9.8315 bps. Terminal `REJECTED_STONE`, not TIER3 or diamond. No historical re-selection of XRP, no 2026 rescue.
Source: branch simple4h-recovery-v0.2, `research/simple4h/MVE_SIMPLE4H_01_2025_CLOSEOUT_V0.1.md`.

5) EMA6H-50X200 Binance OOS 2025-Aug2026: 66 events; mean NET10 +4.3513 bps, NET14 +0.3513 bps; PF NET10 1.0348; bootstrap interval [-109.713,+109.177] bps; 2025 negative, 2026 positive; `TIER3_WATCHLIST`, not robust standalone edge. Other 2H/4H EMA cells often replicated negative, do not retune.
Source: branch ema6h-50x200-regime-dependency-v0.1, `Dream-Account-OS-v2.3-PARTIAL/research/ema6h_50x200_oos/EMA6H_50X200_BINANCE_OOS_2025_2026_001_CLOSEOUT_V0.1.json`.

6) BTC-CONVEX-TREND-CAPTURE-001: untouched historical cross-asset ETH/SOL/BNB replication `SURVIVES` costs incl funding/slippage, but massive 54%-59% MTM drawdowns and PF 1.14-1.27. Historical cross-section expansion and Rising-Regime H2 FAIL; current overall TIER3 FORWARD_ONLY, prospective checkpoint required. Not a small-capital safe route.
Source: branch btc-convex-trend-capture-001-v0.1, `labs/btc-convex-trend-capture-001/FIRST_UNTOUCHED_CROSS_ASSET_CLOSEOUT_V0.1.md`, `.../CHAT_CLOSEOUT_HANDOFF_2026-09-24.md`.

7) HTF DONCHIAN 6H SHADOW 2026: 27 resolved, -0.568923 R, PF .352953; `SHADOW_READINESS_FAIL`. Historical DH03 secondary holdout positive but not rescue of primary. 
Source: branch htf-donchian-shadow-v0.1, `Dream-Account-OS-v2.3-PARTIAL/research/htf_diamond_hunt/HTF_DONCHIAN_SHADOW_001_2026_CLOSEOUT_V0.1.json`.

## Decision after this audit
- No NEW strategy, no NEW backtest, no capital, no market-wide automation launch on this evidence.
- Do not re-run exact rejected vanilla Donchian, Simple4H, or EMA same cells.
- Highest-priority simple *research-only* existing hypothesis: TFG-DONCHIAN-REGIME-ADAPTATION-V1 under its immutable forward freeze, NOT because profitable live but because it tests an economically interpretable low-turnover conditional-market regime without reselecting 2026. Need an operational SOURCE-ONLY check of its original public MEXC endpoint and its original watcher pipeline to establish whether data access/persistence can be restored without altering the scientific source contract. If current post-freeze history is missing, do NOT synthetic backfill or call it forward.
- Independent alternative: monitor the original BTC-CONVEX V0.2 prospective shadow; do not use its historical surviving sibling as forward evidence.
- Rotation/cash risk model was NOT sourced, frozen or tested in this turn; no claims made.
- Before investing: prospective resolved episodes and clear evidence of positive net expected return, PF, losses/drawdown, actual capital feasibility and costs. Zero new live authority.
