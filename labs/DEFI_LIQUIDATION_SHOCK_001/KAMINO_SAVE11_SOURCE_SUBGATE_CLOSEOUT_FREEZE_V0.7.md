# DEFI-LIQUIDATION-SHOCK-001 — KAMINO + SAVE11 SOURCE SUB-GATE CLOSEOUT FREEZE V0.7

Date: 2026-09-23
Status: FROZEN BEFORE CENSUS OUTCOME / SOURCE-ONLY / OUTCOME-BLIND

This closeout is allowed only after:
- census classification = `SQD_EVENT_CENSUS_COMPLETE_PENDING_RAW_SAMPLE`;
- RAW classification = `RAW_SAMPLE_RECONCILIATION_PASS`;
- field enrichment classification is terminal and non-anomalous.

Allowed closeout classifications:

1. `KAMINO_SAVE11_EVENT_CENSUS_RAW_PASS_FIELDS_COMPLETE`
   - field enrichment = `FIELD_ENRICHMENT_COMPLETE`.

2. `KAMINO_SAVE11_EVENT_CENSUS_RAW_PASS_FIELD_GAP_DECLARED`
   - field enrichment = `FIELD_ENRICHMENT_COMPLETE_WITH_SAVE11_PRELAYOUT_PENDING`;
   - the only unresolved field authority is the explicitly frozen Save11 pre-public-layout interval;
   - raw account vectors/data remain preserved and the gap count is reported.

Any source anomaly, key-set mismatch, RAW mismatch, missing chunk or transport-incomplete state forbids closeout.

The closeout MUST report:
- exact authoritative event windows;
- expected and completed daily chunk counts;
- successful instruction counts;
- failed-attempt counts;
- distinct successful signature counts;
- known first-success recovery;
- RAW deterministic sample size/pass counts;
- field-layout counts and explicit missing/pending counts;
- receipt/file hashes where available;
- statement that no economic outcomes were accessed.

This is NOT:
- global `SOURCE_DATA_PASS`;
- Discovery authorization;
- evidence of edge;
- “quase diamante” promotion.

Global DLS remains source-gated until Save0c, marginfi and Drift requirements are adjudicated and FINAL PRE-DISCOVERY AUTHORITY is frozen.

Firewall unchanged: no prices, returns, PnL, direction, trading, orders, wallets, exchange mutation, paid sources, account creation, post-outcome tuning or main merge.
