# ARQ-001-MTF-001 — PRE-OUTCOME IMPLEMENTATION AMENDMENT C V0.1

Date: 2026-09-23
State when frozen: no Discovery trade return, expectancy, PnL or bootstrap result has been computed.

## Frozen bootstrap block semantics

The parent authority's "UTC-day blocks" means exactly one complete UTC calendar day per resampling block.

Procedure:
1. collect unique UTC dates represented by D-confirmed observations;
2. for each bootstrap repetition, sample the same number of UTC dates with replacement;
3. every sampled date contributes all D-confirmed observations for all five ALTs and all 4H event boundaries on that date;
4. compute the pooled BASE12 mean on the resampled observations;
5. repetitions = 10,000; seed = 140001;
6. 95% percentile CI; primary gate requires the 2.5th percentile > 0.

No multi-day block length, iid trade bootstrap, stratified ALT bootstrap or post-outcome alternative is permitted.
