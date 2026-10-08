# TFG-DONCHIAN-REGIME-ADAPTATION-V1 — PROSPECTIVE CAUSALITY / OVERLAP AUDIT
Date: 2026-10-08
Classification: **EXECUTION_INTEGRITY_FAIL / NO_LIVE_GO / ECONOMIC_EDGE_NOT_ADJUDICATED**
Evidence authority: canonical Render service `crypto-edge-radar-v05-canary`, deployed SHA `b9d8e28ff0ec0fe8a67cc9e1970e8c1050c2fa36`, read-only Supabase `crypto-edge-radar-evidence-v05` `public.radar_events` + `public.radar_event_keys` and October 8 Render logs.
Scope: **FORENSIC CLOSEOUT of the current implementation only**. Historical freezes, event chain, and source evidence remain untouched. No SQL mutation, restart, deploy, order, account access, live capital, main merge or parameter tuning.

## Frozen science
Source frozen before first forward evaluation:
- `TFG_DONCHIAN_REGIME_ADAPTATION_V1_FORWARD_FREEZE.json` on `tfg-donchian-1d-oos-2025-v01`.
- 12H long-only Donchian 40; ATR28; signal close > prior 40 highs; stop = signal low - 0.25 ATR28; target = 3R; maximum hold = 80 x 12H bars; one active trade PER SYMBOL; exact next-12H-open entry; BASE 0.20% and STRESS 0.30% round trip.
- Broad bull gate: BTC > SMA200; 200-day SMA rising vs 20 completed days earlier; 4 of 6 assets > SMA100.
- Readiness: >=10 resolved, positive BASE/STRESS expectancy and PF>1, 0 unresolved execution paths, 0 deviations, 0 missed or duplicate signals. No automatic trading authorization.

## Read-only observations
1. Canonical Render status Oct 8: `tfg_forward_metrics.classification=FORWARD_READINESS_GATE_FAIL`; 13 `TFG_FORWARD_SIGNAL` rows, 10 `TFG_FORWARD_RESOLUTION` rows, 3 unresolved; recorded BASE/STRESS -1 R on all 10 resolved => raw displayed -10 R total, mean -1 R, PF=0. All open orders are PAPER, not live orders.
2. Distinct event-key integrity holds and no `TFG_FORWARD_RULE_DEVIATION` or `TFG_FORWARD_MISSED_ELIGIBLE_SIGNAL` entries were observed. **This is not evidence that the forward rule is implemented correctly.**
3. Cross-checking each later entry against the previous signal's recorded exit shows 7 **inadmissible repeat-entry signals** (by symbol), violating the frozen one-open-trade-per-symbol requirement:
   - BNBUSDT: Sep 22 00:00 UTC (Sep 21 12:00 entry still open).
   - BTCUSDT: Sep 22 00:00 (Sep 21 12:00 entry still open).
   - ETHUSDT: Sep 22 00:00 (Sep 21 12:00 entry still open until Oct 7).
   - SOLUSDT: Sep 21 12:00, Sep 22 00:00, Sep 25 12:00, Sep 27 12:00 (Sep 19 00:00 parent entry still unresolved as of Oct 8).
   Thus 13 signal rows comprise only 6 sequentially admissible first entries (four already stopped and two still unresolved), plus 7 forbidden overlapping entries. Among the four first-entry, nonoverlap resolved cases (BNB, ETH, DOGE, XRP), recorded BASE/STRESS outcomes were -1 R each, **descriptive only**, not scientific credit.
4. Another independent failure: `paper_trade.entry_open_time` is identical to the exact 12H signal-close boundary, but the associated append-only signal receipt is written **15.4 to 98.3 minutes after** that time in the observed 13 records (from `radar_events.event_ts`). The watcher currently insists on a fully CLOSED entry 15m candle before it certifies a boundary (`latest_certifiable_signal_close_ms`) and uses that candle's **already-past open** (`materialize_entry`) as a simulated fill. That price was not executable when this decision was recorded. The frozen historical next-open execution assumption is NOT demonstrated by these receipts. Late receipt alone is not proof that a separate true live feed could never execute at boundary; it proves this watcher does not demonstrate such execution.
5. The V0.5 metric implementation only checks duplicate event KEYS, not overlapping positions per symbol or evidence-receipt timestamp > historical open. Consequently it labelled the raw sample as a completed 10/10 readiness gate without recognizing the execution failures (although economics were negative anyway).

## Scientific adjudication
- **This exact forward IMPLEMENTATION is invalid for promotion. STOP.**
- `FORWARD_READINESS_GATE_FAIL` is the current raw runtime label. It must **not** be reworded into a valid `NO_EDGE` for the faithfully executed frozen strategy, because seven transactions violate its frozen single-position rule, and simulated entries use prices already observed before the receipt was recorded.
- Do not revise or erase any recorded losses. Do not reclassify the filtered four as an independently passing sample or retune the strategy.
- Zero capital or micro-live authorization. Full causal execution evidence is missing.
- A NEW prospective execution-corrected evidence epoch, with a separate pre-outcome freeze, new boundary, explicit live-observable fill semantics, and durable state, is required before economic claims. No retrospective repair counts as new forward evidence.
- The current science routing should be `EXECUTION_INTEGRITY_FAIL` (operator-level scientific disposition), distinct from the existing raw app label.

## Reproducible read-only SQL
Only SELECT, no mutations. Inspect signals, resolutions and causal ordering in the canonical Supabase project:
```sql
WITH s AS (
 SELECT k.event_key, split_part(k.event_key,':',2) AS symbol,
        (e.payload_json::jsonb#>>'{paper_trade,entry_open_time}')::bigint AS entry_ms,
        e.event_ts::timestamptz AS receipt_ts
 FROM public.radar_events e JOIN public.radar_event_keys k ON k.event_id=e.id
 WHERE e.event_type='TFG_FORWARD_SIGNAL'
), r AS (
 SELECT k.event_key,
        (e.payload_json::jsonb#>>'{outcome,exit_open_time}')::bigint AS exit_ms,
        (e.payload_json::jsonb#>>'{outcome,base_net_r}')::numeric AS net_r
 FROM public.radar_events e JOIN public.radar_event_keys k ON k.event_id=e.id
 WHERE e.event_type='TFG_FORWARD_RESOLUTION'
)
SELECT s.symbol, s.event_key, s.entry_ms, s.receipt_ts, r.exit_ms, r.net_r,
  round((extract(epoch from s.receipt_ts)*1000-s.entry_ms)/60000.0,1) AS receipt_delay_min,
  EXISTS(SELECT 1 FROM s p LEFT JOIN r pr ON pr.event_key=p.event_key
    WHERE p.symbol=s.symbol AND p.entry_ms<s.entry_ms
      AND (pr.exit_ms IS NULL OR pr.exit_ms>s.entry_ms)) AS overlapped
FROM s LEFT JOIN r ON r.event_key=s.event_key
ORDER BY s.entry_ms,s.symbol;
```

## Root cause in source (SHA b9d8e28)
- `crypto_edge_radar/radar/tfg_forward_watcher.py` loops through all boundaries, repeatedly opens detected signals, and unconditionally appends a signal keyed by (symbol, boundary); no check for a pre-existing open position for that symbol.
- `crypto_edge_radar/radar/strategies/tfg_donchian_regime_forward.py`:`materialize_entry` selects first 15m candle opening at signal-close boundary. `latest_certifiable_signal_close_ms` waits until that same 15m candle CLOSES, making the fill price retroactive.
- `crypto_edge_radar/radar/tfg_forward_metrics.py` computes readiness from all resolutions, without exclusion/blocking of overlap and event-time causality faults.

## Safe remediation and no-rescue
1. Add an immutable **read-only forensic gate** that identifies same-symbol open-position overlaps, event after entry, unresolveds, plus preserved raw metrics, and hard-blocks research promotion; independent QA tests must pass. This is audit-only, not a source/strategy change.
2. Do not quietly change the historical next-open cost/fill contract after outcomes; define and freeze a NEW forward execution experiment with executable decision time and slippage/fill constraints, and no credit from contaminated evidence. Refuse to start it until authority exists.
3. Any new source/delivery service needs a tested single-writer durable persistence route and proof of on-time observations. Do not trigger live trading, restart existing operator bots, or alter canonical Render under this audit.

**VERDICT: IMPLEMENTATION STOP / NOT A PROVEN DIAMOND / NOT AN ECONOMIC NO_EDGE FOR A CLEAN STRATEGY.**
