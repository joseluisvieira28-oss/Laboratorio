# DIAMANTE V8 — BNB Launchpool source-coverage audit (2026-11-16)

## Authority and scope
Standalone additive READ-ONLY source-audit identity. Parent remains BNB-LAUNCHPOOL-DEMAND-001 / frozen Diamond V0.2.
No parent signal, instrument, direction, 15m entry, 24h exit, costs, 60-minute clustering, or 25-event gates are altered.

The inherited source watcher queries only Binance CMS catalogId=48, pageNo=1, pageSize=50.
The old 2026-10-07 receipt observed zero Launchpool titles on that page, and correctly noted it was **not a full historical census**.
Therefore “zero missed events” cannot be an exhaustive post-boundary claim.

## V8 read-only investigation
- Clone and isolate from frozen source-audit branch commit 79f41e0153eda3727f4ced6305d4e457ba3703a2.
- Probe successive Binance CMS pages, up to a safe 80-page cap; record each raw page SHA-256.
- Do NOT infer exhaustiveness from zero on page one or from reaching a page containing articles older than the research boundary.
- Require a proven empty subsequent catalog page with earlier nonempty pages, unique page identities, no provider failure, and valid Launchpool detail lookups.
- If the catalog repeats a page, times out, is inaccessible, changes schema, reaches the cap, or fails any detail lookup: SOURCE_COVERAGE_BLOCKED__NO_ZERO_EVENT_CLAIM.
- Only screen Launchpool titles, then apply the original frozen detail validator for BNB and utility text plus original timestamp.
- Audit may find **historically published** articles; none may be converted into a prospective trade if first observed after its frozen entry time.
- This V8 census cannot certify that body-only Launchpool mentions have all been discovered. Full cross-category/content search requires a separate future source-feasibility authority.
- Do not request price, PnL, Binance account, funding or private order APIs.

## Reproduction and artefacts
- Python: crypto_edge_radar/bnb_launchpool_source_coverage_v08.py
- Offline regressions: crypto_edge_radar/tests/test_bnb_source_coverage_v08.py
- GitHub Actions source-only QA runner uploads JSON in artifacts/bnb_launchpool/source_coverage_v08.
- No protected outcomes or retrospective event selection for Diamond promotion.

## Scientific interpretation
A positive source-census result is a source-coverage finding only. It never changes the scientific Tier 2 / adversarially challenged status and never authorizes market execution, a live bot or Tier 1 promotion.
If the census finds an article not seen at the time of its publication, mark it as a **historical source-coverage gap**. Preserve no-chase and do not backfill.
