# DIAMANTE PURO — BOX-FINANCING-USDC-001 V0.1
Frozen 2026-10-08 before any option/combo BBO or box economics is fetched.
Scope: prospective SOURCE + CURRENT EXECUTABLE QUOTE FEASIBILITY, not historical outcome testing.
Parent audit: ebaddeb5e0ac2922ba523c011c87866f35060409. No old result is reclassified.

## Mechanism and prioritisation fixed before quotes
A long European box buys C(K1), sells P(K1), sells C(K2), buys P(K2), same expiry, K1<K2.
Gross expiry payoff per underlying unit is K2-K1 in USDC under contract performance.
A discount can compensate funding provision, tied capital, exchange/stablecoin risk and balance-sheet constraints.
No directional forecast, IV-RV proxy, future funding assumption or leverage is counted as edge.
This is not VRP: terminal underlying risk cancels algebraically. Not QBC: no spot/future convergence or old threshold reuse.
Prioritise known terminal cashflow, public timestamped liquidity, retail size and capital-normalised economics.
Directional old forwards continue under their own freezes; this mission neither retunes nor opens sealed outcomes.

## Universe and geometry
Deribit production public data only. BTC_USDC and ETH_USDC European linear options.
All currently listed expiries 30 through 120 calendar days from collection start.
At each expiry choose common call/put strike nearest 0.90*current public index and nearest 1.10*index.
Ties choose lower strike. If no distinct valid strikes -> source blocked. No substitute strikes or expiries.
Use maximum minimum_trade_amount across the four legs, only if all contract_size=1 (BTC/ETH) and amount rules consistent.
One initial snapshot census, then one exact-instrument verification snapshot. They are NOT independent trades.
No past settlement, future return, historical price corpus or sealed 2026 outcome is permitted.

## Sources
Allowlist GET /api/v2/public/get_instruments, get_index_price, get_order_book,
get_combo_ids, get_combo_details, get_time only. No auth, create_combo, account, wallet or orders.
Save exact response bytes SHA256, URL, request/receive UTC, RTT, server/quote timestamps.
Metadata/source health is distinct from economic pass.
Require present two-sided uncrossed BBO, positive depth covering minimum amount, correct currency,
instrument identity, quote age <=5s, quartet server timestamp span <=2s.
A stale/incomplete group is INVALID_SOURCE, never zero PnL.
No repeated collection until a positive result; two snapshots only in this experiment.
Network failure gets at most one retry and preserves both attempts.

## Price and fee accounting
Leg-only ask debit = ask(C1)-bid(P1)-bid(C2)+ask(P2).
An indicative four-leg sum is NOT an atomic fill.
Atomic route must be a pre-existing matching long BOX combo with actual orderbook ask and sufficient amount.
Do not treat indicative ticker/leg prices as the combo book. No creating combos.
Public standard option entry fee per leg = min(0.0003*index,0.125*abs(leg premium))*amount.
Use public instrument taker_commission to reconcile 0.0003; discrepancy blocks fee gate.
Separately executed legs pay all four fees. Actual mixed buy/sell combo pays max(sum buy fees,sum sell fees)
only if actual executable combo and individual fee attribution can be verified.
Do not invent rebates, VIP levels or a fee discount for separate legs.
Gross cashflow upper bound = q*((K2-K1)-leg_debit).
Entry-fee-adjusted upper bound subtracts verified four-leg entry fees only.
This is NOT all-cost net: delivery fees, operational cost, latency loss and capital cost are nonnegative omissions.
If upper bound <=0, no extra execution realism can save THAT observed leg route.
Delivery fee conditional on terminal index S is sum min(0.00015*S,0.125*intrinsic_leg(S))*q
over ITM options, subject to documented settlement netting; unresolved netting => do not claim exact all-cost net.
Future generated only by option settlement has no extra futures delivery fee according to current specification.
No funding for options; no assumed borrowing. Negative USDC collateral prohibited in any eventual shadow design.
No exact realised PnL, PF, drawdown or frequency can be inferred from a quote.

## Capital
Quote debit is only a LOWER BOUND on capital. Standard Margin short legs require separate IM;
long option value cannot simply fund short-leg calls. Use documented BTC/ETH SM formulas diagnostically.
Report debit and debit+sum short IM as an indicative initial SM budget, not a liquidation-proof reserve.
Revalue IM at S/index ratios 0.5,1,2 as stress illustrations with intrinsic lower bounds;
exact mark/volatility and path risk remains unresolved. No PM eligibility assumed.
ROI must use committed debit+margin+operational reserve, never notional/margin-only inflated return.
If no positive upper bound or atomic source, no capital allocation is recommended.

## Fixed decision rules
SOURCE_BLOCKED: no admissible atomic quote, absent metadata, stale/crossed book or unverifiable fees/margin.
OBSERVED_LEG_ROUTE_ECONOMIC_REJECT: all valid surveyed leg routes have upper bound <=0.
QUOTE_CANDIDATE_ONLY: positive fully costed atomic quote, known accessible margin, executable size and adverse scenario >0.
Never call a quote DIAMOND, SURVIVES_FORWARD or independent statistical validation.
A profitable financing quote must later beat same-currency cash alternative plus explicit venue/stablecoin risk premium
and operating costs; no arbitrary universal profit/trade-count threshold is imposed here.
No alternative venue/strike/horizon chosen after quotes in this MVE.
If blocked/rejected, archive this exact snapshot test; do not infer all box strategies everywhere are NO_EDGE.

## Next activation
Only a genuinely promising atomic route justifies a new pre-outcome shadow activation:
freeze decision times, size, all costs, full capital, rejection/latency rules, persistence and terminal verification.
No new outcome can be opened under this source/quote-only freeze.

## Boundaries
Research-only. No main merge, live trading, exchange-authentication, account reads, credentials, wallets,
paid services, production Render mutation or post-outcome tuning.
