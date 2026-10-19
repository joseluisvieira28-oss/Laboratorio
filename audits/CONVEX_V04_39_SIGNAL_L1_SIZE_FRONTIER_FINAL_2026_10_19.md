# CRYPTO LAB — CONVEX V04 — 39-SIGNAL HISTORICAL L1 SIZE CAPACITY VERDICT — 2026-10-19

**FINAL RUN:** [GitHub Actions #39200543340](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39200543340) = **SUCCESS** (Linux and Windows synthetic tests, immutable historical source-artifact analysis). Source run [39027126160](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39027126160) = SUCCESS, recovered all resource-blocked Binance USD-M Futures top-of-book archives for original V5 SOL1h/BNB4h historical signals. Original preanalysis freeze `research/convex_l1_capacity_v04/PRE_RATIO_ANALYSIS_FREEZE_2026_10_19.md` committed BEFORE analysing the untouched fractional-capacity ratios. The original full-20% capital-size sufficient counts were previously known, thus this V04 is descriptive in-sample analysis, not new OOS.

## Complete fixed chronological original signal population, 2023-05-16 to 2024-03-30

| Original candidate (separate modelled portfolios) | Source entries | Fresh <=2sec past-only source quotes | Full 20%-equity source best ASK capacity |
|---|---:|---:|---:|
| SOLUSDT 1h | 33 | **32/33 = 96.97%** | **15/32 = 46.875%** |
| BNBUSDT 4h | 6 | **6/6 = 100%** | **3/6 = 50%** |

The single missing SOL prior L1 quote was retained in total historical source denominator. Archives independently confirmed with official publisher SHA256, no reverse chronology or future quote fills. These are Binance Futures quotes, not actual fills, not executable venue transfer to MEXC/Kraken/OKX.

## Four explicit FROZEN static fractional size screens

Proportional trade quantities are static re-interpretations of the exact original V5 source entry quantities that corresponded to 20% paper-equity position notional at 1x. The account returns are NOT recalculated for these scenarios.

| Fraction of original size | Approx static source equity notional | SOL1h enough best ASK | BNB4h enough best ASK |
|---|---:|---:|---:|
| 0.25x | 5% | **24/32=75% — FAIL** | **6/6=100% — SOURCE GATE PASS ONLY** |
| 0.50x | 10% | **20/32=62.5% — FAIL** | **5/6=83.33% — FAIL** |
| 0.75x | 15% | **17/32=53.125% — FAIL** | **4/6=66.67% — FAIL** |
| 1.00x | 20% | **15/32=46.875% — FAIL** | **3/6=50% — FAIL** |

Pre-frozen conditional quote-coverage gate >=95% of whole original eligible population; single-best-ask available size >=90% **among fresh**. SOL 32/33 and BNB 6/6 source availability both PASS; none of the 4 SOL fractions crosses the capacity threshold. BNB only the smallest 0.25x / static 5% size passed, based on just 6 points. This is neither an optimized trading-size rule nor a robust population-wide predictive result.

## New true findings versus mistaken conclusions

1. SOL 1h: even a quarter of original modeled order quantity lacks sufficient best-ASK size for **8/32** fresh entry source snapshots, well below 90% capacity gate. Lowering notional alone in the four predeclared fractions does not validate historical full-quote executable entries. Need **multi-level L2 liquidity, price walking, actual position-size and exit stop funding**, not more V5 tuning.
2. BNB 4h: the fixed 0.25x ratio's entire **6/6** fresh observed source ASK samples contained at least the hypothetical smaller original order size. At 0.50x only 5/6. N=6 is exceptionally thin; cannot promote a sizing strategy from this, and the trade's market impact or realized PnL on BNB remains unverified. This observational difference DOES NOT prove BNB4h is superior to SOL1h or that the smaller size wins money.
3. A best-ASK quote that shows sufficient size can disappear, be stale after retrieval and get depleted by competing orders. A best-ASK quote showing insufficient size doesn't imply the actual taker order cannot fill by walking deeper book levels; its execution price and fee burden are just UNKNOWN.
4. The underlying 2023–25 original parent returns remain retrospective. The 2025 negative SOL1h year, exceptional largest winner concentration, same-asset SOL1h/SOL5m overlapping exposures, weak original nonlatched trail, original MEXC-to-Kraken price/funding portability gaps, and missing authenticated native broker stop ACK are all UNRESOLVED.
5. This is ONLY a re-analysis of the immutable V03C source receipts, with SHA custody; no exchange APIs, public market data requests, no original strategy rerun, no result tampering, no main merge and 2026 holdout SEALED.

## Post-V04 priority that can genuinely improve evidence

**NEXT SCIENTIFIC PREREQUISITE (L2):** Verify authentic, timestamped publisher historical multi-level book depth on exact original SOL/BNB signal timestamps, not website generic fees or one current orderbook sample. Candidate official source OKX historical L2 advertised from March 2023 https://www.okx.com/historical-data ; however V02's accessible catalogue HTTP200 4/4 did NOT yield verified raw source files and later single schema inspection got 403. Need separate pre-source frozen source/terms/entitlement gate, do not claim OKX raw L2 or account trading permissions until proven. A non-matching venue's book cannot be substituted for Binance timestamps without a matching instrument, source alignment and per-venue funding.

**NEXT ECONOMIC TEST ONLY IF L2 VERIFIED:** for every original signal in source era, hypothetically sweep ASK to original qty and reconstruct bid-side protective stop/exit with conservative fees, gaps, latency/funding. Reconcile total executable price and PnL versus original V5 2023–25, retain all invalid episodes; then independent untouched 2026 after separate freeze/authority and prospective broker native stop verification.

## Verdict by asset

- **SOL1h: L1 HISTORICAL SOURCE COVERAGE PASS / FOUR STATIC TOP-ASK SIZE TIERS FAIL / EXACT L2 EXECUTION NOT PROVEN / NO OOS.**
- **BNB4h: L1 SOURCE PASS / SMALL 5%-EQUITY STATIC TIER SINGLE-ASK CAPACITY SOURCE PASS (6/6) / ALL LARGER TIER GATES FAIL / NO OOS.**
- **MONEY MACHINE: NOT CERTIFIED. Trading authority NONE. Real orders/wallets/capital unauthorized.**
