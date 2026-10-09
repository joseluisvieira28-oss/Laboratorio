# CRYPTO LAB — COLHER & BALDE / ASYMMETRIC PAYOFF — VERDICT AUDIT
Date: 2026-10-09
Mode: scientific research, READ-ONLY EVIDENCE AUDIT; NO EXECUTION.
Classification: NO CURRENT TRADING GO. STOP exact rejected/invalid paths; separate unresolved hypotheses preserved.

## Mission
Test whether an automated low-turnover or convex/trailing strategy has independent, realistic NET positive expectancy (small losses, occasional larger wins); avoid selecting winners after seeing protected outcomes. Audit existing families BEFORE inventing parameters or new timeframes.

## Evidence map: immutable and authoritative
1. Original repo audit, 2026-10-08: `audits/OPERATION_SIMPLICITY_2026-10-08_SOURCE_VERDICT_TRIAGE.md` on `audit/science-only-all-fronts-2026-10-08`.
2. TFG-DONCHIAN-1D-001 historical and protected tests: `Dream-Account-OS-v2.3-PARTIAL/research/timeframe_gap/TFG_DONCHIAN_1D_001_2025_OOS_CLOSEOUT_V0.1D.md`, `.../TFG_DONCHIAN_1D_RAPID_VALIDATION_V0.2_STAGE_A_2026_CLOSEOUT.json`, branch `tfg-donchian-1d-oos-2025-v01`.
3. TFG 12H/8H/4H, 3H/2H/1H, and regime V1 closeouts on same branch. DO NOT re-select the 2025 winning timeframe after the known 2026 loss.
4. TFG current runtime forensic: `audits/TFG_DONCHIAN_REGIME_V1_FORWARD_CAUSALITY_CLOSEOUT_2026-10-08.md`, branch `audit/tfg-forward-causality-closeout-2026-10-08`, GitHub forensic run 37839138316.
5. TFG MEXC frozen source probe: workflow run 37838243248: 24/24 sample windows accessible from GitHub Actions. This does NOT demonstrate archive continuity, causal forward observation, or Render source health.
6. BTC-CONVEX first untouched independent ETH/SOL/BNB positive historical basket; XRP/DOGE/ADA/LINK/AVAX untouched expansion FAIL; H2 third basket FAIL. Source: `labs/btc-convex-trend-capture-001/FIRST_UNTOUCHED_CROSS_ASSET_CLOSEOUT_V0.1.md`, `EXPANSION_REPLICATION_CLOSEOUT_V0.1.md`, `H2_RISING_REGIME_CLOSEOUT_V0.1.md`; branch `btc-convex-trend-capture-001-v0.1`.
7. BTC-CONVEX V0.2 authority: `labs/btc-convex-trend-capture-001/PROSPECTIVE_SHADOW_AUTHORITY_V0.2_AGGRESSIVE.md`: Checkpoint A 10 resolved, B 25 with 2 assets >=5, C 50 with 3/4 assets >=5 plus causal/source checks; promotion NEVER automatic.
8. Latest accessible BTC-CONVEX V0.2 snapshot in workflow artifact 11518750694, run 36523792686, JSON timestamp 2026-10-07T23:31:25.776571+00:00, artifact ZIP SHA256 554fa2ce5cfd65027691fa789d75c56ab09c704bf55e0009378fb8d20b5963ba. This is a single snapshot, not a durable append-only full ledger.

## Numeric adjudication
| Exact family | Independent evidence | Frozen result | Decision |
| --- | --- | --- | --- |
| TFG-DONCHIAN 1D unchanged | 2025 OOS 40 trades, mean +0.351084 R, PF 1.5851; day-bootstrap 95% [-0.4273,+1.1005]; much of profit in Q3 | Protected Jan-Aug 2026 30 trades, mean -0.507852 R, PF 0.390577; 16.67% win; 10% hit 3R target | STOP_NO_RESCUE. Not deployable as currently evidenced. |
| TFG 12H/8H/4H and fine 3H/2H/1H | Retrospective/2025 positive cells | Jan-Aug 2026 all these cells fail; 12H -0.533511 R PF 0.377571, 8H -0.614527 R, 4H -0.387946 R | COMPLETE_NO_CELL_PASSES_ALL_WINDOWS; NO timeframe rescue. |
| TFG Donchian12H + broad bull participation regime | 2025 filtered 50 trades +0.405404 R, PF 1.65388; 2026 'filter OFF' diagnostic not pristine | Canonical 2026 runtime shows 13 signals, 10 resolved raw -1R each; 7 overlapping same-symbol entries and 15.4-98.3 min post-entry receipts. | EXECUTION_INTEGRITY_FAIL; current forward cannot establish NO_EDGE for faithfully executed V1. NO live authority. |
| HTF Donchian6H shadow | Earlier DH03 secondary survived frozen historical secondary gate; primary did not | 2026 27 resolved: -0.568923 R, PF 0.352953 | SHADOW_READINESS_FAIL. STOP same exact path. |
| BTC-CONVEX 1H Parent V5 | Untouched ETH/SOL/BNB historical +96%, +91%, +256% base; PF 1.14-1.27; 54%-59% MTM DD | Untouched expansion XRP/DOGE/ADA/LINK/AVAX all negative, mean -75.70%; H2 third basket FAIL | SCOPE-LIMITED, cross-sectional contradiction; historical-only surviving subset is NOT independent live proof. |
| BTC-CONVEX V0.2 prospective | Sep24+ immutable fixed four-asset BTC/ETH/SOL/BNB | Oct7 23:31 UTC snapshot: 1 resolved losing ETH, 3 open; mean equal-weight marked return -0.93155%; 1/50 required for checkpoint C; sources PASS | FORWARD_INSUFFICIENT. NO-GO pending independent forward outcomes. |

## Realism / small-capital and asymmetry
- A 3R fixed target with -1R stop needs 25% wins just to break even before costs; a 16.67% win rate in the protected 2026 1D sample was far below this naive threshold, and actual mean net R was negative. This shortcut is NOT a substitute for realized distribution measurement, time exits or slippage.
- BTC-CONVEX Parent uses roughly 95% of equity allocated per position with a ~4% price stop and ~12% trailing semantics. Nominal stop risk alone is ~3.8% of single-symbol equity before costs/gaps, and historical intra-account MTM drawdowns above 50% occurred. This is not a safe small-capital income system.
- Historical BTC-CONVEX positive test used Binance USD-M perpetuals with 10 bps per side + 2/5 bps slip per side + funding. Do NOT carry the result into MEXC economics without venue/execution equivalence.
- Small capital cannot be rescued with leverage; analyze account-level risk, actual taker fills/spread/depth, min orders, mark-to-market loss, and trading restrictions BEFORE considering execution.
- Evidence of skew is not evidence of a persistent NET edge.

## Scientific verdict — 2026-10-09
CURRENTLY VERIFIED PROFITABLE AUTOMATED STRATEGY IN THIS AUDITED SET: NONE.
GO for live/micro-live on this audit: NO.
NO_EDGE can legitimately attach to the exact tested rejected routes when their source and execution gates passed; DO NOT attach it to untested strategy variants or the causally invalid TFG V1 forward.
TFG V1 current forward: OPERATIONAL / EXECUTION INTEGRITY STOP, not a clean economic falsification of V1.
BTC-CONVEX V0.2: forward unresolved. Never infer economic success/failure from 1 resolved trade.

## Next least-wasteful actions (in order)
1. Preserve all freezes, loss receipts, and source identities unmodified. Close additional historical parameter hunts for the listed rejected families.
2. If the operator wishes to salvage the *scientific question* of Donchian broad-bull V1, do NOT repair existing outcomes. Freeze a NEW execution-valid prospective epoch first, without examining new outcomes; require actual decision timestamp <= quote timestamp <= simulated execution; live-observable bid/ask snapshots from named source after decision; source age bound, separate per-symbol position state, no overlapping entries, audit append-only. Then minimum sample and interval gates.
3. BTC-CONVEX V0.2: keep original forward boundary/universe/costs, inspect genuinely newly resolved causal receipts and independently validate their persistence and history-vs-replay properties; only act at frozen checkpoints 10/25/50. A startup_failure is an operational CI failure, not an edge verdict.
4. Any NEW economic hypothesis must have a materially different mechanism, preregistration, independent assets/periods, and separate accounting; do not rescue existing failed outcomes by changing 3R, entry filters, fees or timeframes.
5. Operational publication/readiness reports and regression PASS statuses receive ZERO profitability credit.

## Governance
No trades, funds, exchange accounts, wallets, Render mutation/deploy, data purchase, main merge, protected holdout opening, or signal/cost retuning were executed in this audit.
Research branch notes only; no claim of new scientific forward observations or a live-trading authority.
