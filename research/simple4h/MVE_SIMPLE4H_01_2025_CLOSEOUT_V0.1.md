# MVE-SIMPLE4H-01 — 2025 ONE-SHOT CLOSEOUT V0.1

Date: 2026-09-17
Status: FINAL RESEARCH CLOSEOUT
Branch: `simple4h-recovery-v0.2`

## Scope

This closeout covers only the predeclared 2025 confirmation run for the seven frozen 4H cells recovered from Simple Trading V0.1.

2026 remains locked. Live trading remains unauthorized. No exchange mutation, wallet action, alert/webhook, or merge to `main` is authorized by this closeout.

## Provenance

Frozen authority / gate commit: `26b32dc31d2bc844b49e5c0c0ce340f1968c70c1`

GitHub Actions run: `35191566407`

Workflow artifact: `MVE_SIMPLE4H_01_2025_ONE_SHOT_V03`

Artifact SHA256: `6e19680ac5708ed2f415031d08913104d2f3de56da77a87dc1005eb1022a184b`

Source manifest SHA256: `6951be900952a7dc902e024ac13427bd33c6e41fd65f5ab68e56987cbb3045eb`

Source gate: 52 checksum-verified Binance Data Vision USD-M Futures monthly 1m archives covering 2024-12 warm-up plus 2025-01 through 2025-12 for BNBUSDT, DOGEUSDT, SOLUSDT, XRPUSDT.

## Independent audit

The downloaded artifact digest matched the GitHub Actions artifact digest exactly.

The source manifest produced by the source-only gate and the source receipt used by the economic one-shot were byte-identical.

The event ledger contained exactly 633 completed trades across the seven frozen cells. Every entry and exit timestamp was inside calendar year 2025. No 2026 timestamp was present. No overlapping trades were found within any cell. `net10_bps = gross_bps - 10` and `net14_bps = gross_bps - 14` held for every event.

All summary statistics were recomputed independently from the event ledger, including means, medians, profit factor, one-sided t-tests, 95% confidence intervals, max drawdown, quarterly stability, BH-FDR q-values, circular moving-block bootstrap lower bounds, concentration flags, cell classifications, and family classification. The recomputation matched the published summary with zero numeric discrepancies.

## 2025 results

| Cell | N | Net10 mean (bps) | Net14 mean (bps) | PF net10 | Positive quarters | BH q | Bootstrap lower95 (bps) | OOS positive | Strong evidence |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| Donchian — BNBUSDT | 76 | 8.8056 | 4.8056 | 1.0536 | 1 | 0.7217 | -78.7775 | No | No |
| Donchian — DOGEUSDT | 84 | -17.5162 | -21.5162 | 0.9505 | 2 | 0.7217 | -146.1109 | No | No |
| Donchian — SOLUSDT | 78 | -5.8315 | -9.8315 | 0.9783 | 2 | 0.7217 | -129.7782 | No | No |
| Donchian — XRPUSDT | 76 | 53.0538 | 49.0538 | 1.2388 | 3 | 0.7217 | -78.3893 | Yes | No |
| EMA Pullback — SOLUSDT | 116 | -57.3075 | -61.3075 | 0.7404 | 1 | 0.9191 | -115.0306 | No | No |
| EMA Pullback — DOGEUSDT | 106 | -1.4456 | -5.4456 | 0.9929 | 3 | 0.7217 | -88.6143 | No | No |
| Extreme Mean Reversion — DOGEUSDT | 97 | -13.8554 | -17.8554 | 0.9323 | 2 | 0.7217 | -90.8097 | No | No |

Family metrics:

- valid cells with N >= 50: 7/7
- cells with N >= 100: 2/7
- clean OOS-positive cells: 1/7
- strong-evidence cells: 0/7
- cells negative after 14 bps costs: 5/7
- median Net14 across adequate cells: -9.8315 bps
- quasi-diamond review eligible: false

## Final adjudication

`REJECTED_STONE`

The recovered Simple Trading 4H family did not confirm as a robust economic edge in the protected 2025 confirmation period under the frozen rules and costs.

The XRPUSDT Donchian cell was economically positive in 2025, but it did not achieve strong evidence: BH-FDR q = 0.7217 and bootstrap lower95 = -78.3893 bps. It therefore cannot be promoted, isolated, or used to rescue the family without creating post-outcome selection.

No Tier 3 watchlist promotion. No Tier 2 promotion. No quasi-diamond promotion. No production or live-trading authorization.

## Governance disposition

The 2025 one-shot authorization was consumed and subsequently disarmed. 2026 remains unopened and locked for this hypothesis. Reopening, tuning, narrowing to XRPUSDT, changing costs, changing thresholds, or creating a new confirmation period from this result would require a genuinely new preregistered hypothesis and must not be represented as continuation of MVE-SIMPLE4H-01.

Close this recovery path without merge to `main`.
