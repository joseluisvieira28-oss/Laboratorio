# CRYPTO LAB — RADAR CONTINUITY & NET EDGE TRIAGE
Date: 2026-10-10 | Source: **actual** canonical Supabase Postgres + GitHub Actions + Render; research-only.
Authority: no orders, capital, exchange account reads, frozen-rule modification, post-outcome tuning, look-ahead, outcome reopening, or 2026 holdout unsealing.

## Executive economic verdict (as observed; not a final scientific closeout)
**NO verified independent, account-fee-inclusive positive forward economic edge demonstrated by these Radar candidates today.**
Do NOT conflate: a successfully deployed collector, CI test, Telegram delivery, a historical benchmark, a trade entry, or a PUBLIC_EXECUTION_SAMPLE_READY_FOR_AUDIT with profit.

### OPTIONS-SPOTPERP-001-V2.1: cost removal DOES NOT rescue observed 19 cases
Canonical persisted `OPTIONS_V21_FORWARD_RESOLUTION`: 19 rows, **19 unique event keys**; first persisted Sep 21, latest Oct 10 01:25 UTC.
- Mean `base_net_bps`: **-25.22966**; stress mean **-35.21050**.
- Mean original **`scaled_gross_bps=-15.24882`**. This **already has zero reference fees subtracted** and is **negative**. Gross winners 10/19, base-cost winners 8/19.
- All cases respect ledger's frozen effective weight; 2 rows have `weight=0.9828160354` and `weight=0.9807795465`, hence effective base cost **9.82816** and **9.80780 bps**, not 10. The naive `base+10=-15.22966` differs slightly from authoritative `scaled_gross=-15.24882`; use **ledger gross**, not an approximate universal 10 bps correction.
- Scientific `options_v21_metrics.py` has a **pre-frozen gate of first 50 resolutions** plus 5 ten-trade blocks, minimum nonnegative blocks 3, concentration and PF gates. **19/50 -> cannot prematurely close out as formally failed or approve/promote**; the negative gross descriptive is strong adverse evidence.
- 2025 tier2 benchmark referenced in code: mean +5.04277 bps with 10-bps base cost (historical only); 2026 forward sample does not reproduce it yet.
- Public execution observation sample 14, nonfunding taker/spread proxy approx **16.01189 bps** round-trip; neither authenticated account fee receipt nor all-in real cost confirmation. Do not use public proxy as realized MEXC expenses. Current observed gross mean negative even under the unrealistic zero-transaction-cost scenario.

### TFG-DONCHIAN-REGIME-ADAPTATION-V1: FAILED readiness gate
- 12 persisted `TFG_FORWARD_RESOLUTION` rows, **12 distinct keys**; **12/12 have `outcome.base_net_r=-1`**, mean BASE and STRESS both **-1.0R**.
- Parent `tfg_forward_metrics.py` requires mean and PF >0 plus integrity, zero overdue paths/deviations/missed signals.
- This is **FORWARD_READINESS_GATE_FAIL** with no positive forward economic support. Don't change rule/timings to rescue. Additional developments require a separately preregistered, economically different mechanism, not tuning.

### Other Radar fishing candidates: insufficient/no defensible verified net edge
- CED1D-0031: persisted **14** `CED1D_RENDER_SHADOW_V03_RECEIPT`, **2** historical `CED1D_RENDER_SHADOW_V03_FAILURE` (latest Oct 10 09:09 UTC), including **source 404** for `AVAXUSDT-bookDepth-2026-10-08.zip`. Gate frozen **60 resolved events AND 8 complete UTC weeks**, not satisfied. Source blocked ≠ economic NO_EDGE.
- BNB-LAUNCHPOOL-DEMAND-001: no qualifying causal measurements against frozen 25; WAITING_GENUINELY_PROSPECTIVE_EVENT.
- ETF-CME-INSTFLOW-001: **Q4-2026 forward outcomes sealed until 2027-01-01 00:00 UTC**. Source-only verification permitted; no interim P&L or PF claims.
- HTF-DH03, EMA6H etc: no forward net edge certification on this read. Absence of evidence is not proof of no edge.

## Measured persistence / infrastructure hazard
Read-only SQL on project `jqzdvgjeuveiktftyrlz` at **2026-10-10 13:28:39 UTC**:
- **2,680 total immutable events**, newest `RADAR_RUNTIME_LIVENESS` event at **12:45:22 UTC**; 43+ minute staleness at the observation time.
- **25** persisted `RADAR_RUNTIME_GAP_DETECTED` receipts, mean recorded **117.15 min**, worst **244.79 min**, **12** recorded gaps >120 min. They are receipts, not necessarily 25 independent downtime incidents. Breakdown 10 Oct 5; 9 Oct 11; 8 Oct 2; older 7.
- Example latest recovered gap: 2026-10-10 **09:15:25.432 → 12:35:07.592** UTC (11,982.16 sec = 199.70 min). Earlier same day 05:30:19.799 → 09:04:21.524 (12,841.725 sec = 214.03 min). Across days worst 244.79 min.
- Follow-up 12:45 cycle labeled `CONTINUOUS` only for latest bucket, **does not adjudicate any previous missed eligible event window**.
- Render `crypto-edge-radar-v05-canary` Free plan, branch `crypto-edge-radar-postgres-v0.5`, autoDeploy off. On Oct10 initial deploy commit `b9d8e28ff0ec0fe8a67cc9e1970e8c1050c2fa36`; new truthful-health PR #173 merged into same base at `9a6b5384bdf45fc9faf5faf9bbe63f03a3e196bf`, triggered read-only shadow deployment `dep-db53sllckfvc738sas10` (verify lifecycle separately). **Merge/build does not prove runtime healthy or live 24/7.**
- Main Telegram keepalive PR #174 merged at `4c73d16e70a92b52588297ca82de853ab8faf6e2`. Operator verified message delivery. It probes public endpoint via Actions; cannot repair missed collector windows.
- GitHub scheduled workflow `*/8 * * * *`, empirically runs far less frequently than configured and may time out on Render cold starts; GitHub formally warns scheduled executions can be delayed or dropped under load ([docs](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)).
- CED1D 404 for `https://data.binance.vision/data/futures/um/daily/bookDepth/AVAXUSDT/AVAXUSDT-bookDepth-2026-10-08.zip`: SOURCE_INCOMPLETE; never forge this archive or pretend normal collector progress. A later `health=OK` may formerly have hidden retained CED failure; PR #173 fixes the status reconciliation.

## Economics gate decision board
| Family | Frozen gate & evidence | Observed | Today |
| --- | --- | --- | --- |
| OPTIONS V2.1 | 50/50 plus temporal PF/mean/concentration; account route costs unknown | 19/50; base -25.23 bps; zero-model-cost ledger gross -15.25 bps | CONTINUE FROZEN FORWARD; DO NOT AUTHORIZE AUTO-LIVE; NO COST EXCUSE FOR CURRENT LOSS |
| TFG DONCHIAN | >=10 + positive base/stress R/PF + clean integrity | 12/12 -1R | FORWARD READINESS FAIL; NO RESCUE/TUNING |
| CED1D | 60 events + 8 UTC weeks, source complete | 14 receipts, 2 failures; 404 missing | SOURCE_BLOCKED; CANNOT DECIDE EDGE |
| ETF CME | 2026-Q4 sealed until 2027-01-01 | 2 historical source observations; 1 expected miss | ONLY SOURCE WORK; INTERIM P&L FORBIDDEN |
| BNB | 25 true prospective causal measurements | 0 | EVENT_WAIT; NO CLAIM OF EDGE |

## Authorized next engineering and source work (strict order)
1. **Evidence truth (deploy verification)**: confirm merged PR #173 Render build completes on expected commit, verify post-deployment state, `health` degrades when persisted collector fails, all safety flags false, and no account/orders. Fail closed on stale state.
2. **Continuity diagnosis**: inspect trigger timing, Render free idle/suspend behavior, liveness gaps and restart/collector times. Preserve every missed window as `MISSED_EVIDENCE_REVIEW_REQUIRED` until checked. Do not retroactively invent signals.
3. **CED source gate**: verify exact Binance Vision archives and checksum provenance for missing dates without replacing frozen source, without remote API account keys, without fabricated rows. If 404 persists: SOURCE_BLOCKED, not strategy dead.
4. **Scheduler reliability**: GitHub schedules are best effort, Telegram warnings are not an always-on collector. Prioritize genuinely continuous single-writer runtime with deterministic recovery and durable storage. No new paid service, plan or resource until bounded trade-off and explicit cost approval.
5. **Profit-first gate**: inspect forward gross before fee-model arguments, then authentic account fee / funding / spread / slippage / latency / risk only if a candidate demonstrates gross positive economics on preregistered unseen outcomes; read-only account evidence requires explicit route scope. A frozen 50-sample tier gate governs OPTIONS final disposition.
6. **Controls**: global 24/7 collector status, science OOS status, live account/PC order exit state and trading authority are **four separate dimensions**. This document authorizes **none** of them.

## Reproducibility — example read-only queries (never update/rewrite Postgres)
```sql
SELECT COUNT(*) n, COUNT(DISTINCT payload_json::jsonb ->> 'event_key') unique_event_keys,
       AVG((payload_json::jsonb ->> 'scaled_gross_bps')::numeric) gross_mean_bps,
       AVG((payload_json::jsonb ->> 'base_net_bps')::numeric) base_mean_bps,
       AVG((payload_json::jsonb ->> 'stress_net_bps')::numeric) stress_mean_bps
  FROM public.radar_events WHERE event_type='OPTIONS_V21_FORWARD_RESOLUTION';
SELECT COUNT(*) n, AVG((payload_json::jsonb #>> '{outcome,base_net_r}')::numeric) base_r
  FROM public.radar_events WHERE event_type='TFG_FORWARD_RESOLUTION';
SELECT COUNT(*) n, MAX((payload_json::jsonb ->> 'gap_seconds')::numeric) max_gap_sec
  FROM public.radar_events WHERE event_type='RADAR_RUNTIME_GAP_DETECTED';
```

No market entry recommendation, backtest cherry picking, past outcome refreeze, automatic promotion, or claim of current account balance is made.
