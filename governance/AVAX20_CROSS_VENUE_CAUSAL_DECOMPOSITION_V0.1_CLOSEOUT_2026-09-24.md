# AVAX20 CROSS-VENUE CAUSAL DECOMPOSITION V0.1 — CLOSEOUT — 2026-09-24

**Parent candidate:** CED1D-0031 — AVAXUSDT Momentum 20D CONTINUATION H1  
**Freeze:** `AVAX20_CROSS_VENUE_CAUSAL_DECOMPOSITION_V0.1_FREEZE_2026-09-18.md`  
**Workflow run:** `35649164799`  
**Artifact:** `avax20-cross-venue-causal-decomposition-v01`  
**Artifact ID:** `10661723788`  
**Artifact digest:** `sha256:4e4b52dd795d4a0b047da1490a0b2c25df3de1c9890d1af508623deef8c93ffc`  
**Result fingerprint:** `cbeefdd78c631099dc4ba026f357c9e37405a5b7e0c5bd21d6a2370ca9a0a9a6`

## Frozen classification

`FOUR_OF_FOUR_CROSS_EXECUTION_SURVIVAL`

Diagonal reconciliation: **PASS**.

## Signal-source concordance

- Binance signal days: 357
- OKX signal days: 357
- union signal days: 357
- intersection signal days: 357
- same-direction intersection: 357
- opposite-direction intersection: 0
- Binance-only signal days: 0
- OKX-only signal days: 0
- exact directional Jaccard: **1.0**

Under the frozen 2025 corpus, the signal identity is therefore venue-invariant between the tested Binance and OKX perpetual sources.

This does **not** establish temporal independence. Both signal sources cover the same 2025 inference period.

## Frozen 2x2 economic decomposition

### BINANCE SIGNAL → BINANCE EXECUTION
- N = 357
- BASE funded mean = +8.5506754938 bps
- BASE PF = 1.0477360430
- STRESS funded mean = +2.5506754938 bps
- positive active months = 7/12
- weekly bootstrap lower 95% = -41.0125112315 bps
- frozen economic survival = PASS

### BINANCE SIGNAL → OKX EXECUTION
- N = 357
- BASE funded mean = +8.3038578191 bps
- BASE PF = 1.0463580530
- STRESS funded mean = +2.3038578191 bps
- positive active months = 7/12
- weekly bootstrap lower 95% = -41.2424125451 bps
- frozen economic survival = PASS

### OKX SIGNAL → BINANCE EXECUTION
- N = 357
- BASE funded mean = +8.5506754938 bps
- BASE PF = 1.0477360430
- STRESS funded mean = +2.5506754938 bps
- positive active months = 7/12
- weekly bootstrap lower 95% = -41.0125112315 bps
- frozen economic survival = PASS

### OKX SIGNAL → OKX EXECUTION
- N = 357
- BASE funded mean = +8.3038578191 bps
- BASE PF = 1.0463580530
- STRESS funded mean = +2.3038578191 bps
- positive active months = 7/12
- weekly bootstrap lower 95% = -41.2424125451 bps
- frozen economic survival = PASS

## Interpretation

What this experiment supports:

1. The exact 20D continuation signal did not depend on choosing Binance versus OKX as the signal-source venue in the frozen 2025 corpus.
2. The economics survived execution transfer in both directions under the frozen BASE14 and STRESS20 accounting.
3. The positive effect was not an artefact of one tested execution venue.
4. The result therefore strengthens the candidate's **mechanism/transportability evidence**.

What it does not support:

1. It is not a new untouched time OOS block; all four quadrants use the frozen 2025 inference period.
2. The weekly bootstrap lower bound remains below zero in both execution venues, so statistical uncertainty is not erased.
3. It does not replace the genuinely prospective CED1D M6 gate.
4. It does not automatically produce Tier 1, micro-live, production, or capital authority.

## Diamond Test V1 mapping

Cross-venue causal/transport fingerprint: **PASS**.

The remaining decisive Diamond evidence remains the already-frozen prospective Render gate:

- >=60 resolved prospective events;
- >=8 complete UTC signal weeks;
- >=50 complete execution pairs;
- reference BASE mean > 0 and PF > 1;
- reference STRESS mean >= 0;
- >=50% complete weeks positive;
- execution BASE mean > 0 and PF > 1;
- execution STRESS mean >= 0;
- median leg latency <=1000 ms;
- p95 leg latency <=5000 ms;
- mean nonfunding proxy <=14 bps;
- p95 nonfunding proxy <=20 bps;
- book snapshot coverage >=99%;
- book capacity coverage >=99%;
- every active month capacity >=95%;
- frozen concentration gates pass.

Until those prospective gates resolve, Diamond state remains:

`DIAMOND_TEST_COLLECTING__CROSS_VENUE_FINGERPRINT_PASS`

## Governance

- no post-outcome venue dropping;
- no signal or timeframe change;
- no cost reduction;
- no 2026 historical backfill;
- no live trading;
- no orders;
- no exchange mutation;
- no wallets;
- no leverage authorization;
- no merge to main from this closeout.
