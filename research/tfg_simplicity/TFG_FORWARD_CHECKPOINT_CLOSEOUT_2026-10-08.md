# TFG-DONCHIAN-REGIME-ADAPTATION-V1 — PUBLIC-RUNTIME CHECKPOINT CLOSEOUT
Date: 2026-10-08
Audit timestamp: 2026-10-08 20:13:59 UTC
Branch: `ops/tfg-regime-source-gate-2026-10-08`
Status: **FORWARD_READINESS_GATE_FAIL — NOT MICRO-LIVE ELIGIBLE**
Scope: public/read-only diagnostics and immutable freeze review; **not** a new hypothesis, backtest, or change in scientific rules.

## Canonical authorities
- Frozen primary: `TFG_DONCHIAN_REGIME_ADAPTATION_V1_FORWARD_FREEZE.json` on `tfg-donchian-1d-oos-2025-v01` (12H long-only Donchian40, ATR28, 3R target, 80 x 12h maximum hold, baseline 0.20% and stress 0.30% roundtrip, gated by BTC SMA200 rising and 4/6 breadth).
- First eligible signal strictly post freeze 2026-09-16T15:16:53Z.
- Deployed public canonical runtime: `https://crypto-edge-radar-v05-canary.onrender.com/health`, read-only snapshot. Git commit reported in runtime `b9d8e28ff0ec0fe8a67cc9e1970e8c1050c2fa36`.
- Research remained outside main, deployed runtime, private account API and capital.

## Experiment 1 — source access, provider contract unchanged
Isolated GitHub Actions workflow `TFG Regime Frozen MEXC Source-Only Probe V0.1`, run https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37837579316, SUCCESS.
- **24/24 strict source sample checks PASS** across 6 frozen spot symbols x 4 windows: recent 15m, 15m at first post-freeze boundary, past 1d for regime SMA warmup, recent 1d.
- Validated original public unauthenticated `GET https://api.mexc.com/api/v3/klines`, original provider-native timestamp semantics.
- Important limitation: four small windows per symbol; not a full candle-gap census; proves source accessibility **from GitHub Actions only**, not from Render. Did not evaluate market outcomes or prove liveness and persistence.

## Experiment 2 — current canonical public runtime
Isolated public read-only status workflow `TFG Regime Public Canary Status Audit V0.1`, run https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37837874163, SUCCESS; telemetry `2026-10-08T20:13:59Z`, Radar last cycle `2026-10-08T20:13:40Z`.
- HTTP 200; `health=OK`; `mode=PUBLIC_SHADOW_ONLY`; `evidence_backend=postgres`.
- `orders_created=false`, `live_capital_enabled=false`.
- `resolved_forward_trades=10` of frozen minimum 10; `unresolved_execution_paths=3`, all `MATURING_WITHIN_FROZEN_MAX_HOLD` (zero overdue/unclassified).
- Reported BASE: total **-10.0 R**, mean **-1.0 R/trade**, PF **0.0**.
- Reported STRESS: total **-10.0 R**, mean **-1.0 R/trade**, PF **0.0**.
- `missed_eligible_signals=0`, `rule_deviations=0` in the current aggregate; duplicate-signal check PASS, duplicate-resolution check PASS.
- Gate checks that FAIL: base expectancy >0; base PF>1; stress expectancy>0; stress PF>1; unresolved paths=0.
- Gate checks that PASS: minimum resolved >=10; rule deviations=0; missed signals=0; duplicate event counts=0.
- Canonical machine classification: **FORWARD_READINESS_GATE_FAIL**. `readiness_gate_pass=false`. The 3 still-maturing exits cannot be silently treated as outcomes; no trading authority.

## Audit of seemingly suspicious -1R values
The deployed engine's `_net_r(entry,exit,risk,cost_pct)` uses
`net_R = (gross_return_fraction - cost_fraction) / (risk_fraction + cost_fraction)`.
On a stop price `exit = entry * (1-risk_fraction)`, `gross=-risk_fraction`; thus `net_R=(-risk-cost)/(risk+cost)=-1` for BOTH BASE and STRESS.
Therefore identical -1R BASE/STRESS values are mathematically consistent with loss-at-stop normalization; they do **not**, on their own, prove a calculation defect. This aggregate view does not expose individual exit reasons: do not assert 10 distinct STOP fills without reading their source-bound ledgers.

## Scientific evidence integrity limitation — essential
The deployed `TFGForwardShadowWatcher.run_once` loads historical public candles through the present and loops every 12H boundary beginning at the FIRST post-freeze boundary on every invocation. For any missing `TFG_FORWARD_SIGNAL` key it can append a late reconstructed signal and, in the same cycle, a resolved outcome. Its `append_once` ensures idempotency but not observation-at-T0. The canonical public health metrics aggregate event payloads and do not expose the database `event_ts` required to prove signals were recorded at T0.
Consequently, **the public 10/10 count alone is NOT sufficient to certify causal forward provenance**. Auditing `event_ts` of signal receipts against each `signal_close_utc` and execution window is required. Any retrospective inserted signals must be classified as backfill/descriptive, excluded from confirmatory prospective validation; existing historical gates may not be modified to rescue.
No direct database access was used because Render workspace identity was not selected/authorized.

## Decision (do not overstate)
1. **Definite operational gate verdict today:** `FORWARD_READINESS_GATE_FAIL`; NOT micro-live eligible, no live capital, no trading.
2. The observed 10-resolved-trade economic profile is decisively negative at the initial frozen minimum. There is no basis to claim a money machine or diamond.
3. **NOT justified:** claim that all 10 are independently observed causal forward trades; conclude universal/permanent NO_EDGE for trend following; reselect the favorable older windows; alter EMA/SMA breadth thresholds, costs or target; launch live; or silently include 3 open episodes.
4. For a higher-authority *causal* scientific verdict, perform a read-only proof of each persisted signal `event_ts` versus `signal_close_utc` on the authorized runtime evidence store. Do NOT mutate or rebuild receipts to pass this check. Resolve the remaining 3 under the frozen rule for descriptive completeness if they mature.
5. Priority recommendation: **STOP promotion/deployment of this exact route at this checkpoint.** Do not rebuild it as a new 2026 winner from its historical results. Any new hypothesis must be economically different and genuinely preregistered.

## Links
- Source gate code: https://github.com/joseluisvieira28-oss/Laboratorio/blob/ops/tfg-regime-source-gate-2026-10-08/research/tfg_simplicity/tfg_mexc_source_only_probe_v01.py
- Live public-runtime diagnostic code: https://github.com/joseluisvieira28-oss/Laboratorio/blob/ops/tfg-regime-source-gate-2026-10-08/research/tfg_simplicity/tfg_public_runtime_probe_v01.py
- Source run: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37837579316
- Canonical public-state run: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37837874163
- No main merge, order, exchange mutation, wallet/account operation or deployment was performed.
