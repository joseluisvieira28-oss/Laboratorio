# CRYPTO LAB — NEGATIVE EDGE MAP V0.1

**Snapshot:** 2026-09-27  
**Scope:** meta-analysis of existing Crypto Lab evidence only. No new market hypothesis was tested.  
**Primary source:** Drive `CRYPTO_LAB_EDGE_CLASSIFICATION_BOARD_V1 — 2026-09-17` (LAB_BOARD + GAP_MAP), updated 2026-09-27.  
**Legacy source:** Drive `CRYPTO ARCHIVE INDEX — CLOSED / DISCARDED LABS — 2026-09-13`.  
**Governance:** research-only; no main merge, live trading, exchange mutation, protected-outcome opening, or post-outcome rescue.

## 1. Why this exists

Negative evidence is a research asset. The purpose of this map is to stop the lab from repeatedly spending time on mechanisms that have already failed under independent or high-volume tests, while keeping SOURCE_BLOCKED, INSUFFICIENT_SAMPLE and technical failures scientifically distinct from NO_EDGE.

This document introduces an exploratory **Failure Density** and a conservative **MECHANISM_EXHAUSTED** rule. Neither is promotion evidence and neither may be used to rewrite historical verdicts.

## 2. Canonical board snapshot

The current LAB_BOARD contains **68 canonical rows**.

- **26** = NEGATIVE_SCIENTIFIC
- **9** = POSITIVE_OR_SURVIVES
- **1** = MIXED
- **10** = INSUFFICIENT_SAMPLE
- **15** = BLOCKED_OR_TECHNICAL
- **7** = PENDING_OR_FORWARD

Strict adjudicated set = scientific negatives + positive/survives = **35 rows**.

Exploratory overall Failure Density = **26 / 35 = 74.3%**.

### Important limitation

Board rows are **not independent statistical observations**. Some rows aggregate families, some are children of older mechanisms, and maturity differs. Failure Density is therefore a routing/portfolio-of-research diagnostic, not a market probability or p-value.

## 3. Failure Density by primary family

| Family | Neg | Pos/Survives | Strict adjudicated | Failure Density | Interpretation |
|---|---:|---:|---:|---:|---|
| VOL | 6 | 3 | 9 | 66.7% | Mixed evidence; family not exhausted |
| TREND | 4 | 2 | 6 | 66.7% | Mixed evidence; family not exhausted |
| MICRO | 1 | 1 | 2 | 50% | Small-N: do not generalize |
| FLOW | 3 | 1 | 4 | 75% | Mixed evidence; family not exhausted |
| MR | 1 | 0 | 1 | 100% | Small-N: do not generalize |
| RV | 1 | 1 | 2 | 50% | Small-N: do not generalize |
| CREDIT | 2 | 0 | 2 | 100% | Small-N: do not generalize |
| ACCESS | 3 | 0 | 3 | 100% | High negative density; inspect mechanism-level evidence |
| SUPPLY | 2 | 0 | 2 | 100% | Small-N: do not generalize |
| CARRY | 1 | 0 | 1 | 100% | Small-N: do not generalize |
| EVENT | 1 | 1 | 2 | 50% | Small-N: do not generalize |
| LEADLAG | 0 | 0 | 0 | NA | Small-N: do not generalize |
| MACRO | 1 | 0 | 1 | 100% | Small-N: do not generalize |

The family-level table is deliberately **not** an exhaustion verdict. Example: MR has a superficially high negative rate among adjudicated rows, but most MR rows are actually source/sample limited, so the family remains open.

## 4. Conservative MECHANISM_EXHAUSTED rule

A narrowly defined mechanism can be labeled `MECHANISM_EXHAUSTED` only when all conditions hold:

1. At least **3 independent terminal scientific negatives spanning >=2 genuinely distinct data blocks/labs**, **or** one large exhaustive family-scale screen plus >=2 independent terminal confirmations.
2. No contradictory survivor exists inside the same narrow mechanism definition.
3. SOURCE_BLOCKED, DATA_FAILURE, PROVENANCE_FAILURE, TECHNICAL_FAILURE and INSUFFICIENT_SAMPLE contribute **zero** exhaustion credit.
4. The label applies to a **specific mechanism + observable + horizon/structure**, never automatically to an entire primary family.
5. Reopening requires **materially new information**: a new economic mechanism, information primitive, venue/market structure, causal source, or execution geometry. A new threshold, indicator setting, fee assumption, subperiod, or cosmetic timeframe is not enough.

## 5. Negative map — zones to stop re-mining

### A. MECHANISM_EXHAUSTED — generic short/medium-horizon price-only technical mining

**Scope:** generic candle/indicator/pattern/price-only continuation or reversal at intraday / short-medium horizons, especially repeated parameterized technical variants.

Evidence includes:
- Pattern Lab V1: 3,600 hypotheses, 0 survivors.
- Scalping V1–V5.1: repeated NO-GO / negative expectancy.
- SCL-AGG-002: 0/240 combinations survived; best Discovery mean approximately +2.47 bps became approximately -2.92 bps in validation before costs.
- Classic Indicators Gap Lab: primary textbook-indicator queue failed frozen gates.
- MVE-ICHIMOKU4H-01: closed NO_EDGE.
- Simple Trading 4H: independent 2025 one-shot REJECTED_STONE.
- MVE-ADX4H-01: 2025 confirmation failed.
- GTL third-touch 1H: terminal Discovery failure.
- USORB 15m: 2,853 trades, negative gross and net economics.

**Boundary:** this does **not** kill higher-timeframe trend/asymmetry. Donchian 1D/DH03 and CED AVAX20 provide contradictory survivor evidence outside this narrow exhausted zone.

**Routing rule:** do not open another RSI/EMA/MACD/VWAP/ADX/Ichimoku/Bollinger/breakout/pullback combination merely by changing thresholds or timeframe inside the already-covered short/medium-horizon technical surface.

### B. MECHANISM_EXHAUSTED — generic linear BTC→ALT / follower lead-lag mining

**Scope:** generic follower-response / linear lag dependency using already-public price/return/positioning transforms, without a new information channel.

Evidence includes:
- H180-0001: zero BH-FDR survivors and zero net-positive at 14 bps.
- Legends LL-0001 and LL-0002: NO_EDGE.
- H03 cross-venue replication: failed independently.
- LL-0017-TPD-001: 2023 Discovery NO_EDGE; all four quarters negative, 1/6 assets positive.
- Historical lead-lag/follower lines repeatedly failed to survive correction or economic costs.

**Boundary:** Coinbase–Binance exact historical tick work and INFORMATION-PROPAGATION-GRAPH-001 are source-blocked/forward-required and do not add negative evidence. A genuinely new asynchronous information surface may reopen the question under a new LAB_ID.

### C. NEGATIVE_DENSE — raw macro/event direction without richer state

Evidence includes CPI/NFP no-edge lines, NFP Surprise V2 2025 independent OOS failure, Treasury Auction Demand failure, and historical macro-transmission failure.

**Interpretation:** event occurrence or simple signed surprise is often insufficient. The missing layer is more likely conditional state: point-in-time expectations, rates repricing, pre-positioning, liquidity and multi-asset transmission.

**Routing rule:** no more “event happened -> BTC direction” labs without a materially richer causal information set.

### D. NEGATIVE_DENSE — generic access/structure shock -> directional price response

PERPETUAL-LAUNCH-SHOCK, MSEL-001 and BINANCE-COLLATERAL-HAIRCUT all failed their frozen mechanism/economic gates.

**Boundary:** do not generalize to all ACCESS. MSEL-002 remains source/schema blocked; a new mechanism must be structurally distinct.

### E. COST_DOMINATED — small gross effects that disappear under executable frictions

Repeated pattern:
- Stablecoin Peg Dislocation: gross sign approximately +2.47 bps, destroyed by 20/30 bps cost envelopes.
- Spot–Perp Cash-and-Carry: gross convergence existed but OOS net economics were negative after realistic costs.
- Scalping/AggTrades: small discovery effects unstable even before costs.
- Treasury Auction Demand: effect too small after costs/inference gates.
- Multiple technical strategies: nominal gross effects fail 10–20+ bps economic hurdles.

**Routing rule:** a mechanism whose plausible gross edge is only a few bps should not receive expensive OOS/holdout budget unless the execution model is independently credible and the effect has large headroom over friction.

### F. REPLICATION_FRAGILE — Discovery beauty frequently collapses later

Examples:
- MVE-ADX4H-01: earlier promise, 2025 confirmation negative.
- NFP Surprise V2: independent 2025 OOS materially negative.
- BTC Options Expiry Reversal: independent OOS / robustness failed.
- AAVE-LIQUIDATION-OVERHANG: 2023 mechanism pass disappeared in 2024.
- USOPEN-VOL exact post-ETF replication failed one confirmatory leg even though the broader clock effect remained visible.

**Routing rule:** Discovery strength must never substitute for independent temporal evidence.

## 6. What is NOT dead — the inverse map

### OPEN / UNDER-RESOLVED

**CREDIT / borrower-state stress**  
Old Aave rate-stress and overhang formulations failed, but HF crowding and liquidation-convexity/oracle-distance use materially different borrower-state mechanics and are still outcome-blind/forward accumulating.

**MICRO / forced flow with canonical source**  
L2-RESILIENCY replicated as a mechanism; liquidation and order-book families are still mostly source/calibration limited. This is not a generic taker-flow reopening.

**VOL / clock-conditioned persistence and forecast state**  
Generic squeeze/expiry/directional-vol ideas have many failures, but CIRV-HAR intrawweek forecast and U.S.-open persistence survived meaningful later gates. Monetization remains separate and fragile.

**RV / naturally hedged, low-turnover dislocations**  
OPTIONS-SPOTPERP remains a Tier 2 candidate, while naive cross-market composite/fade formulations failed or were sample-limited. Future RV must use direct economics, not cosmetic composite states.

**FLOW / slow institutional or structurally constrained flow**  
ETF-CME institutional flow survived to Tier 2, while generic on-chain/shortflow/cross-chain directional mappings often failed. Distinguish predictive persistent flow from contemporaneous flow.

**MR / dense economic anchors**  
Do not call MR exhausted. Stablecoin peg was cost-dominated, while stETH/WBTC/rETH variants were mostly provenance/sample limited. The opportunity is a different, dense, executable anchor with enough untouched events.

**MACRO / expectations + transmission**  
Raw event direction is negative-dense, but a defensible point-in-time expectations + rates/liquidity transmission layer remains the materially distinct unresolved question.

## 7. New lab preflight — mandatory negative-map gate

Before any new lab:

1. Map the proposed lab to `Primary Family + mechanism + observable + horizon + execution geometry`.
2. Search the classified snapshot and legacy negative evidence.
3. If it lands inside `MECHANISM_EXHAUSTED`, reject unless the proposal explicitly identifies the materially new information primitive.
4. If it lands in `COST_DOMINATED`, require pre-outcome friction headroom.
5. If it lands in `SOURCE_LIMITED` or `SAMPLE_STARVED`, solve feasibility before outcomes.
6. If it lands in a mixed/open region, define the exact distinction from failed siblings before freezing.
7. Never use a new threshold, subperiod, asset slice or fee assumption as the sole justification to reopen a dead mechanism.

## 8. V0.1 conclusions

The strongest cross-lab pattern is not “crypto has no edge.” It is narrower and more useful:

- **Generic public price transforms are heavily mined and usually fail after independent validation/costs.**
- **Contemporaneous movement/flow is frequently descriptive rather than predictive.**
- **Small-bps edges are structurally vulnerable to friction.**
- **Rare-event economic anchors often die from sample scarcity before they can be adjudicated.**
- **Source provenance is itself a major research bottleneck and must not be mislabeled NO_EDGE.**
- **The surviving/open frontier increasingly uses distinct economic information: institutional positioning, market structure, borrower state, option/volatility state, clock-conditioned mechanisms, and direct relative-value economics.**

Negative evidence is therefore promoted from archive material into an **anti-duplication routing layer**.

## 9. Source integrity

Canonical Drive sources used:
- Edge Classification Board ID: `1fv3S6nawlOUePlcR7TQXb4aqnois1nxuVeDTeUuS8fM`
- Crypto Archive Index ID: `13E2foZjzmROlc8p1eKRndooOsCKZ__rmHWLCbBLz0WY`
- Scalping Recovery Registry ID: `1ia9DLUtpYCjkmdkNR9DW2G-dUjQNJjN3mV3sJhxW_L8`

Generated companion files:
- `LAB_BOARD_CLASSIFIED_V0.1.csv`
- `FAILURE_DENSITY_BY_FAMILY_V0.1.csv`
- `LEGACY_NEGATIVE_EVIDENCE_V0.1.csv`

## 10. Governance status

**V0.1 meta-analysis complete.**  
No historical verdict changed.  
No protected outcome opened.  
No live trading / exchange mutation / main merge authorized or performed.  
The `MECHANISM_EXHAUSTED` labels in this document are **new routing labels**, not replacements for the original scientific verdicts.


## 11. Drive mirror

Canonical working mirror created in Google Drive:
- Title: `CRYPTO LAB — NEGATIVE EDGE MAP V0.1 — 2026-09-27`
- Drive ID: `17QO40pQLtaImmUxJUVeUU7jCCH3hNewdJK6uAs-gwNc`
- URL: https://docs.google.com/document/d/17QO40pQLtaImmUxJUVeUU7jCCH3hNewdJK6uAs-gwNc/edit

The GitHub branch remains the versioned implementation/evidence surface. The Drive document is the operator-readable mirror.


## 12. Governance integration

The canonical Drive board `CRYPTO_LAB_EDGE_CLASSIFICATION_BOARD_V1 — 2026-09-17` was updated additively in `RULES!A15:C15` with a mandatory **Negative Edge Map preflight**.

The rule requires every new lab to consult this V0.1 map and complete `NEGATIVE_MAP_PRECHECK_V0.1`; it also explicitly preserves the distinction between scientific negative evidence and `SOURCE_BLOCKED`, `DATA_FAILURE`, `PROVENANCE_FAILURE`, `TECHNICAL_FAILURE` and `INSUFFICIENT_SAMPLE`.

No existing rule, historical verdict, lab status or protected outcome was modified.
