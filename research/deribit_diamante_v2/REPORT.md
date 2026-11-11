# CRYPTO LAB — DERIBIT DIAMANTE V2: economic feasibility verdict
2026-11-02. **CANDIDATE NOT VALIDATED — GO ONLY FOR PROSPECTIVE RESEARCH.**
No positive net expected return has been demonstrated. Source access and arithmetic have been independently reproduced; they are not economic alpha. No universal negative conclusion about BTC options is warranted either.

## A. Source and inheritance
Public repository verified. Inherited draft PRs [327](https://github.com/joseluisvieira28-oss/Laboratorio/pull/327), [328](https://github.com/joseluisvieira28-oss/Laboratorio/pull/328), [329](https://github.com/joseluisvieira28-oss/Laboratorio/pull/329), [330](https://github.com/joseluisvieira28-oss/Laboratorio/pull/330) remain distinct source witnesses. Original linear raw artifact13147450267 SHA256838e99db9d7d36ebf4304e4ca261023ec90e6abbe984a618c187854b892ba782 reproduced4/4, including deterministic selection from2952 summaries/12 eligible pairs. No fresh price is substituted into that original receipt.

V2 freeze [e34ad073](https://github.com/joseluisvieira28-oss/Laboratorio/commit/e34ad0732abf1574735006b33307ddf5653fbaa9) precedes8 new anonymous production GETs and all prospective outcomes. [Source + independent audit workflow41486828544](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41486828544) SUCCESS, source implementation53b6fa159ce66daf757664cee42cc0c03bd0dde2. All4 books open, metadata multiplier1 BTC, minimum/amount increment0.01, both currenciesUSDC. lot_size1 is NOT the minimum order. Tick5USDC through1000,20 above1000. Raw metadata retained.
New observation2026-11-02 16:59:54–56UTC, index77388.43USDC/BTC, expiry2026-11-06 08:00UTC. Source book timestamps span1592ms, within precommitted3s comparison gate. This is near-contemporaneous, NOT atomic execution, arbitrage or guaranteed fill. Small targetq=.01 per leg; top depth meets it. Original13:49 and V216:59 must NEVER be treated as a synchronized price comparison.

## B. Four mechanisms and one choice
| Mechanism | Finding | Decision |
|---|---|---|
| Unconditional long straddle | Clear terminal payoff, measurable premium erosion/cost, no positive EV evidence | Independent control C0 only |
| Long strangle | Lower premium, wider dead zone, proportionately more fee friction in SAME V2 session | No separate development now; not universally disproven |
| Lagged realized displacement vs option price | Test whether a causal lagged empirical terminal-distribution forecast predicts intrinsic proceeds above full ask costs | Single P1 candidate, unvalidated |
| Volatility events | No preregistered calendar/surprise uplift net of premium found in this investigation | Do not build another system or mine event outcomes |

P1 is a long ATM straddle held to expiry ONLY when a fixed60-prior-daily-return forecast net of delivery costs exceeds entry all-in by20%. It is not delta-hedged volatility trading. High realized volatility retrospectively, or an IV/RV gap, cannot establish future expected profit. Forecast is a simple hypothesis, not a certified fair value model. Forecast uses underlying delivery returns only as causal predictors, not as executable option-price history or recycled Crypto Lab strategy holdout performance.

## C. Real economics
SAME V2 session, q=.01 each long option. QuotesUSDC per1BTC contract:
| Structure | Call BID/ASK; strike | Put BID/ASK; strike | Ask premium | Entry fees | Entry all-in | Instant spread+4fees | Relative friction |
|---|---|---|---:|---:|---:|---:|---:|
| Straddle |1280/1300;77500|1320/1360;77500|26.60|0.46433058|27.06433058|1.52866116|5.74685%|
| Strangle |655/675;79000|760/780;76000|14.55|0.46433496|15.01433496|1.32866992|9.13175%|

Standard taker fee per leg=q*min(.0003*that book index,.125*option price), no discounts. Long-only combos get no combo-fee discount. Per-book indexes are77388.43 for ATM and77389.16 for OTM; preserved separately, no false identical index assumption.
Instant BID sale proceeds26.00/14.15; exit fees0.46433058/0.46433496. These hypothetical roundtrips measure immediate crossing loss, NOT maximum strategy loss.

Expiry payoff=q*(max(S-Kcall,0)+max(Kput-S,0)), whereS is officialBTC_USDC delivery TWAP07:30–08:00UTC. Friday ITM delivery fee=q*min(.00015*S,.125*intrinsic) per ITM leg, no fee for worthless options. Official daily/non-Friday exemptions are preserved. Automatic option-to-future-to-USDC settlement has no second delivery charge on the generated future absent other positions. Forced liquidation fee is a different concept and is NOT used for normal expiry.

| Structure | Lower/upper expiry breakeven, no extra slippage | One adverse tick all-in | Two ticks +1.5x trading fee all-in |
|---|---|---:|---:|
| Straddle |74782.34959 /80218.46583|27.46433058|28.09649587|
| Strangle |74487.39339 /80513.51052|15.11433496|15.44650244|

Relative to fresh index, straddle needs terminal movement below−3.3675% or above+3.6569%; strangle below−3.7487% or above+4.0382%. These are terminal bounds, NOT “touch the level intraday and win”. One-tick straddle bounds74742.35559 /80258.47183; strangle74477.39489 /80523.51202. Source is ephemeral and slippage is stress modelling, not empirically measured fill quality.
Max loss before adverse ticks is the full entry all-in27.06433/15.01433USDC. Premium paid in full, no leverage/other positions assumed. Funding, blockchain, withdrawal, conversion, tax and USDC/fiat risks are not measured; the frozen study measures venue-level returns only, not a deployable all-in personal return.

Net terminal scenarios, entry at original ASK, no additional slippage, all entry/delivery fees:
| Official terminalS | Straddle netUSDC | Strangle netUSDC |
|---:|---:|---:|
|70000|47.83066942|44.88066504|
|75000|−2.17683058|−5.12683496|
|78000|−22.18133058|−15.01433496|
|81000|7.81416942|4.86416504|
|85000|47.80816942|44.85816504|

Inherited original78000-strike witness is separately reproduced: entry25.60 +0.46745022=26.06745022USDC; expiry roots75381.94769/80618.83785. Net at78000=−26.06745022; at75000=+3.82004978; at81000=+3.81104978. Its1.33490044 instantaneous loss is not the amount needed to make expiry profitable.
Early selling would require a future executable BID and future index-dependent sell fee; no current book or mark is used to invent that future price.

## D. History and evidence boundary
Official API specification SHA256d6f9c44990222ff6e78b21862a37996a1230e50a9dc4bb4063e98ebeaa7a3e34 inspected and catalogued inHISTORY_SOURCE_CATALOG.json. Public get_order_book supports instrument_name/depth only, with no historical as-of parameter. Public trade tape demonstrates trades, not a standing executableBID/ASK for our size. Marks/IV/candles are valuation/trade summaries; index charts/daily delivery prices describe the underlying/settlement. Private historical orders concern user accounts and are outside scope.

No adequate free official executable quote archive was identified. This is a scoped search result, not a proof that no archive exists anywhere. Therefore NO historical executable options backtest is produced.100 officialBTC_USDC past daily delivery prices were actually obtained; their availability supports the causal forecast input, not a historical option execution claim.

Today is2Nov;6Nov expiry is still FUTURE. Zero prospective P1 settled observations, zero OOS economic observations, no confidence interval or drawdown estimate that can support an edge. Do not turn source PASS into economic PASS.

## E. Independent audit and practical verdict
Independent audit.py does NOT import probe.py: Decimal calculations plus closed-form piecewise fee roots vs primary float/bisection; independently reselects original and fresh instruments, verifies12 original/new raw SHA bodies, reconstructsBBO/depth/fees/payoff/scenarios. Agreement<1e−8USDC. This is implementation independence within the same investigation, not a second human or an independent market sample.
7 adversarial local tests: original friction/roots, expiry vs force liquidation, fee cap and daily exemption, tampered hash, stale/wrong/insufficient book, future forecast input exclusion, missing delivery remainsUNSETTLED, tick-grid threshold crossing. InitialCI ran6 tests; added tick-crossing regression and an offline replayCI validate final code without another market sample. The correction addresses valid tick grids at1000USDC; it changes no frozen scientific threshold or observed economics.

**GO for one bounded research experiment. NO economic promotion. Candidate remains unvalidated.**
No order/account access, private brokerage credentials, spend, merge or main modification. Main SHA matches inherited source base75fb36c8337c3221b7551c513e049cd472dad231.

## F. Receipts and preservation
- Original source run41456328296 /artifact13147450267; original ZIP SHA838e99db9d7d36ebf4304e4ca261023ec90e6abbe984a618c187854b892ba782.
- New source+audit run41486828544 /artifact13162880426; ZIP SHA62d57ca258a56742e959e6a394b7224d775d0eb404f385cf220ecbd4cc658117.
- Public raw original and V2 ZIPs preserved under evidence/ on this research branch so Actions artifact expiry does not erase provenance.
- OBSERVATION_2026-11-02.json, INDEPENDENT_2026-11-02.json and rawmanifest insideZIP make all reported numbers reproducible.

## G. One concrete next experiment
Daily prospective next-day ATM straddle P1 vs same-quote unconditional C0, entry08:05UTC with5min operational window. Freeze details are authoritative.20 development +20 confirmation sessions, thenOOS. No threshold fitting between phases. Success requires>=120 valid OOS sessions,>=60 selected entries,>=180days and>=6months OOS, positive preregistered block-bootstrap lower95% bounds for P1 and pairedP1−C0, stress survival, monthly consistency and drawdown limits. Otherwise no promotion. Economically negative upper bound rejects THIS hypothesis; insufficient samples or ambiguous CI means inconclusive, never “all options impossible”.
A dedicated daily task is enabled, beginning3Nov2026 at08:05UTC (09:05Paris/Swiss winter time), bounded365 sessions. **Scheduled, not yet operationally proven:** task timing/runtime/connectors may fail. Late attempts must be recordedMISSED_SESSION, sources failingSOURCE_BLOCKED, no backfill or pretend captures. First real prospective receipt must verify end-to-end operation. No result will arrive “automatically certified”; separate recalculation remains mandatory.
Commands:
```sh
python research/deribit_diamante_v2/probe.py entry --out /new/unique/session
python research/deribit_diamante_v2/probe.py settle --entry /immutable/entry/receipt.json --entry-sha256 ORIGINAL_HASH --out /new/unique/settlement
```
Current7Nov/six-month returns cannot be manufactured today. Next useful checkpoint is whether the first scheduled prospective session can preserve a valid, immutable decision before its next-day expiry.

## Official references checked2Nov2026
- https://support.deribit.com/hc/en-us/articles/31424932728093-Linear-USDC-Options
- https://support.deribit.com/hc/en-us/articles/25944746248989-Fees (updated2Nov13:58UTC; announced5Nov daily maker waiver does NOT reduce our taker fees or Friday option fees)
- https://docs.deribit.com/api-reference/market-data/public-get_instrument
- https://support.deribit.com/hc/en-us/articles/38507223482781-API-guidance
- https://docs.deribit.com/api-reference/market-data/public-get_order_book
- https://docs.deribit.com/api-reference/market-data/public-get_delivery_prices
- https://docs.deribit.com/specifications/deribit_openapi.json
- https://docs.deribit.com/articles/accessing-historical-trades-orders
- https://docs.deribit.com/articles/options-data-collection-best-practices
- https://support.deribit.com/hc/en-us/articles/25944487427741-Restricted-Jurisdictions
- https://support.deribit.com/hc/en-us/articles/26327903944221-Investor-classification

Switzerland does not appear on the inspected public restricted-country list. That does NOT confirm individual derivatives eligibility, KYC, legal suitability or onboarding; those remain unverified. No login was attempted.

## Final verification
Draft [PR331](https://github.com/joseluisvieira28-oss/Laboratorio/pull/331) created. Final offline [CI41488007563](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41488007563) SUCCESS at code commit98316f23e39c445790ba36805849716097e93d6d:7 tests, both archive ZIP hashes, original/new raw hashes and independent economics reproduced with ZERO market requests. Main rechecked unchanged. Scheduled forward has not yet run; zero prospective economic outcomes.
