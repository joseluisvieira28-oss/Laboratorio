# DIAMOND TRADFI — terminal feasibility verdict
Research date: 2026-10-20. Retrieval interval: 09:37–09:40 UTC (11:37–11:40 Zurich); minute precision only, not exchange timestamps. FREEZE commit b65a9986f48d40dac48f7803402d771878b90926 precedes price inspection. PIVOT commit 10a7be1ceafa7800eb1308ae389828140dc3472c follows quote-source failures. Correction: PIVOT's typed 09:40 timestamp was rounded forward; actual retrieval-clock check was 09:39:48 after that commit. Use GitHub server commit times for exact ordering. Neither file is rewritten.

**Verdict: SOURCE_BLOCKED / INSUFFICIENT_EVIDENCE. Zero provisional candidates. Not NO_EDGE for the entire mechanism.**

## Case and authentic document trail
Priority Technology Holdings (NASDAQ PRTH); buyer WD Capital Partners Parent, controlled by CEO Thomas Priore. Buyer funds conditional cash consideration, economic compensation is for waiting and bearing deal-break risk, not free arbitrage.
SEC 8-K: https://www.sec.gov/Archives/edgar/data/1653558/000121390026101651/ea0306047-8k_priority.htm
Agreement: https://www.sec.gov/Archives/edgar/data/1653558/000121390026101651/ea030604701ex2-1.htm
Agreement section 3.1: USD8.05 cash; section 8.1: outside date Dec 18 2027. Shareholder/disinterested votes, money-transmitter regulatory consents and continuing credit agreements are material conditions. No financing condition does not remove completion risk. Reverse fee is paid to company, not a guaranteed shareholder put.
Issuer Sep 21 announcement: https://ir.prioritycommerce.com/news-releases/news-release-details/priority-technology-holdings-inc-announces-definitive-agreement
Forecast H1 2027; 38% premium to Sep18 close and 65% to Nov7 2025 pre-initial-proposal close. Neither premium is the capturable spread. Conditions and forecast are statements as announced, not independently certified current completion status.

## Prices: explicit evidence conflict
Nasdaq summary https://www.nasdaq.com/market-activity/stocks/prth and /historical return data unavailable.
Actual issuer links /stock/stock-quote-chart and /stock/historical-price-lookup returned 403. Earlier guessed /stock-information paths also failed and are not evidence of actual endpoint failure.
Secondary https://www.financialcontent.com/quote/NQ%3APRTH/historical search result reports Oct19 2026 close 7.81, volume 462044. Opening redirect https://www.financialcontent.com/quote/NQ:PRTH/historical instead returns Sep22 last 7.805 and Sep21 close 7.80, Sep18 close 5.83. This is a cached-vintage conflict; Oct19 price is NOT promoted to a validated current observation. Other secondary search results show Oct16 close 7.82, not an independent exchange verification.
No contemporaneous ask/size, no fill, no synchronized official pending-status/price pair. A real published historical close is observed (Sep21 7.80), but is stale; at that historical close contractual spread is 3.2051%, not current executable economics. No price-series strategy or protected holdout evaluated.

## Conditional economics — USD base, not an execution claim
Using the disputed secondary Oct19 observation P=7.81 solely as sensitivity:
cash C=8.05; gross gain 0.24/share = 3.072983%. Cash is conditional on completion.
Official example tariff https://www.interactivebrokers.com/en/pricing/commissions-stocks.php : Pro Fixed 0.005/share, USD1 minimum, 1% maximum/order; qualifications/extra applicable fees remain. This is an example, not the user's broker or a global cheapest-fee floor. Do not apply USD1 unconditionally to tiny orders.
100 shares: reference principal USD781; entry commission USD1 =0.128041%; conditional gain after entry commission only USD23 =2.944942% of reference principal (2.941176% of USD782 cash outlay). Not full net.
One whole share reference cash 7.81 plus capped example commission 0.0781 =7.8881 before other frictions, if whole-share access exists. Fractional/corporate-action eligibility unverified. 200 shares reference USD1562; example entry fee USD1. No economically required capital minimum established.

Full friction ledger: entry commission quantified above; ask-minus-close, slippage, market impact UNKNOWN; conversion and reconversion FX costs UNKNOWN (USD cash assumed, no claim CHF risk absent); custody/mandatory-action charges UNKNOWN; taxes/withholding depend on investor and UNKNOWN; failure exit commission/regulatory fees UNKNOWN until venue/path; financing excluded by unlevered design; opportunity cost not zero. Thus a full numerical cost floor cannot be certified; unknown is not zero.
Sensitivity, NOT observed costs: assume additional aggregate friction 0.25%, 0.5%, 1% => 2.6949%, 2.4449%, 1.9449% after entry commission only, before opportunity/tax/event loss.
At hypothetical 4% annual cash opportunity cost, after entry commission and opportunity cost: 90 days +1.9586%; 180 +0.9723%; 365 -1.0551%, before remaining frictions. Gross simple annualization 12.4627%, 6.2313%, 3.0730%, respectively. 90 days is optimistic sensitivity; H1 forecast implies roughly 73–253 days from Oct20; no promised close date. Outside-date delay is longer still.

## Failure risk — no estimated success probability
Sep18 historical close 5.83 is a pre-definitive-announcement proxy, NOT truly unaffected: initial proposal was already public. Drop from 7.81 to5.83: -25.3521%, USD1.98/share; one loss consumes 8.25 successful gross spreads.
Using issuer rounded 65% premium gives approximate truly unaffected 8.05/1.65=4.8788, not an exact observed historical close; indicative drop -37.5315%. No guarantee of either recovery level.
Mechanical stress -30%, -50%, zero recovery => losses USD234.30,390.50,781 for100 shares before exits.
Two-state breakeven success probability with break5.83: (7.81-5.83)/(8.05-5.83)=89.1892% before costs; 89.6396% with USD0.01/share entry fee, higher with delay/costs. This is an algebraic threshold, NOT a forecast or probability inferred from spread.
Frozen gross-spread/binary-loss screen does not reject this case on its own (0.24/1.98=12.12%, above5%). Promotion instead FAILS on quote integrity, full costs and independently supported event-risk probability. Do not claim negative EV without probability evidence.

## Discovery ledger — source-biased, not a census
Bounded searches: October2026 all-cash acquisitions; SEC September/October cash mergers; issuer corroboration. No complete SEC-wide population reconciled.
- PRTH announced Sep21: earliest verified eligible discovered announcement, selected before prices (agreement signed Sep18).
- MGLD Sep25: SEC discovery 000149315226044491; later, not selected.
- SSTI Sep29: issuer discovery cash plus CVR; excluded.
- SYNA Oct1 amendment: SEC 000114036126038294; later/revised pre-window original, not selected.
- OPCH Oct6: SEC 000110465926113904 and issuer confirmed; later, not selected.
- PCRX Oct8: SEC 000110465926114571; later, not selected.
- PAG Oct15: secondary-only discovery, unverified, not selected.
- ACVA Sep10 outside window and completed Oct16 (SEC 000119312526423478); SLP completed Oct6 (SEC 000102345926000092); excluded.
- WBD completed Oct6 (SEC 000119312526415055); original announcement not established in window; excluded.
- Trumid Oct19 private target/mixed cash-equity (SEC 000119312526425378); excluded.
- BLFS July21 mixed consideration (SEC 000119312526408201); Open Lending June announcement, HSII Oct2025, Premier Sep2025, ITM private/stock, AbbVie target completed Sep3: excluded on date/structure/status.
No performance average, success rate, survivor universe or best-across-all-deals claim supported.

## Single pivot: index forced flows
Official archive https://press.spglobal.com/index.php?l=25&s=2429 inspected through Oct19.
Oct1 release: https://press.spglobal.com/2026-10-01-Vylor-Added-to-the-S-P-500-Twilio-Set-to-Join-S-P-500-Others-to-Join-S-P-MidCap-400-and-S-P-SmallCap-600 effective Oct1/6.
Oct5: https://press.spglobal.com/2026-10-05-Freshworks-Set-to-Join-S-P-SmallCap-600 effective Oct8.
Both already past at capture; excluded, no historical returns opened or retuned.
Targeted S&P/Nasdaq searches for upcoming Oct21/22/23/26 and November changes found no verified eligible upcoming case. This is bounded search failure, NOT proof none exist globally.
ETF issuer https://www.ishares.com/us/products/239774/ishares-core-sp-smallcap-etf confirms IJR tracks S&P SmallCap600, establishing a potential benchmark-following mechanism. It does not prove forced purchase size, timing, price-insensitive execution or a profit payable to a speculative buyer.
Fallback classification: NO_ELIGIBLE_EVENT_VERIFIED / INSUFFICIENT_EVIDENCE, not economic rejection. No price spread invented, no third pivot.

## Rational next action
Do not build a bot or deploy capital. To reconsider this particular merger requires a new timestamped official ask/size, reconciled current filings and complete broker-specific cost ledger plus justified failure-risk assessment. To investigate flows needs an authentic upcoming announcement and prospective pre-event observation. No automatic monitor created. Stop this bounded run with the above source-blocked verdict, no claim mechanism exhausted.
Audit limitations: URLs and bounded observations preserved here, not raw HTTP payloads or byte-authenticated source hashes. Search/open caching conflicts explicitly retained. Arithmetic reproducible from formulas and calculations.json; no CI result used as economic evidence. Existing closed studies untouched.
