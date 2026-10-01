# Marginfi Orca execution feasibility — integrity gate and preliminary venue audit
Date: 2026-10-01
Branch: dls-marginfi-route-migration-v01
Classification: ORCA_EXECUTION_FEASIBILITY_SIGNAL_AUTHORITY_BLOCKED
No new market-outcome authority. No scientific promotion.

## Binding integrity verdict
The handoff's +9.6396 bps SHORT premise is not supported by the cited executable provenance.
GitHub run 36816846032 has head fcfdaf9badff8aa1cd762d017ff6445cbd73a2ce.
Its workflow checks out github.sha. At that exact commit, source/run_marginfi_orca_impact_dev_v0_1.py implements:
    gross = exit_open / entry_open - 1.0
    entry_exec = entry_open * (1 + slip)
    exit_exec = exit_open * (1 - slip)
    net = (ratio - 1.0) - fee * (1.0 + ratio)
This is LONG arithmetic labeled SHORT. Current corrected code cannot retroactively validate that run.
The existing QUARANTINE document already prohibits inference from this run.
The TERMINAL_CLOSEOUT's directional interpretation is superseded by this integrity audit.
The handoff's quoted figures are not recomputed here and are not a valid SHORT cost budget.
No quarantined ledger/receipt/outcomes downloaded or recalculated.

## Independent causal-availability defect
Cascade membership links successive events with gaps <= five minutes.
A retrospective final event at t cannot be known to be final until strictly after t+5 minutes (plus source completeness/watermark latency).
The frozen entry A is the next full minute after t, at most 60 seconds later.
Thus it enters before cascade termination can be known, using future absence of events.
This defect remains after correcting return signs.
Example source-only synthetic check: t=12:00:10; A=12:01:00; earliest termination knowledge strictly after 12:05:10.
Entry precedes knowledge by at least 250 seconds.
A causal entry after the quiet period changes the frozen signal mapping; it is not a silent implementation fix.
Do not amend existing families, move entries, mirror LONG, rerun Jul-Sep, or lower gates.
A separately motivated causal family must be frozen before a legitimately authorized untouched outcome.

## Source evidence preserved
No challenge to Marginfi→Orca route migration or signed-flow source PASS.
Source-pass authority is distinct from market-direction and execution authority.
Oct-Dec V0.2 remains INSUFFICIENT SAMPLE; no Development.
2025/2026 remain protected.

## Official base-fee screening (bps per side; no VIP/staking assumptions)
Venue | Maker | Taker | Taker/Taker RT fee floor | Status
Binance USD-M USDT | 2 | 5 | ~10 | Above hypothetical 9.6396 mean before friction
Bybit non-VIP | 2 | 5.5 | ~11 | Above hypothetical mean before friction
OKX level 1 | 2 | 5 | ~10 | Above hypothetical mean before friction
Kraken Derivatives base | 2 | 5 | ~10 | Above hypothetical mean before friction
Coinbase International public tier 10 | 2 | 4 | ~8 | Hypothetical residual ~1.6396 bps; unproven
Hyperliquid base | 1.5 | 4.5 | ~9 | Hypothetical residual ~0.6396 bps; unproven
Bitget regular | 2 | 6 | ~12 | Above hypothetical mean before friction
Gate VIP0 | not adjudicated | 5 | ~10 | Above hypothetical mean before friction
Lighter Standard API | 0 | 0 | 0 | Promising external execution lead; NOT execution PASS
Lighter Plus | 0.5 | 0.5 | ~1 | Promising external execution lead; NOT execution PASS
Lighter Premium, zero staked LIT | 0.4 | 2.8 | ~5.6 | External lead; NOT execution PASS

Fee floors are approximate because exit notional differs. For a linear SHORT:
r = exit_exec / entry_exec
net = 1-r-fee_entry-fee_exit*r-funding-other_costs.
If equal fees f and no slippage, net = g-f*(2-g); break-even f=g/(2-g).
Using the disputed g only as arithmetic illustration gives about 4.8221 bps/side.
That is not an empirically authorized budget. Median, CI, folds and causal implementation still gate survival.

Lighter official API account-types documentation explicitly allows Standard API accounts, zero fees and 300 ms taker latency; Plus 300 ms and Premium 140 ms. These are venue delays, not total source-to-fill latency.
Official public websocket supplies orderbook snapshots/deltas every 50 ms and nonce continuity checks.
This supports a possible prospective public-data acquisition route, not historical reconstruction proof.
No wallet, signup, account switch, authenticated request or order was made.
Published main-interface terms do not name Switzerland in the prohibited-country list; this does not certify account eligibility, legal availability, or other-interface eligibility.

## Unresolved feasibility dimensions — fail closed
No venue has execution PASS in this audit.
Contract listing/identity, current SOL minimum notional, tick/step, historical availability, account-specific fees and jurisdiction must be captured from official instrument/account authority before a freeze.
SOL listing is established in the existing Binance market authority, Kraken contract specifications and Gate group-A announcement; exact metadata for other routes remains unverified.
Tiny size does not establish low spread/slippage during liquidation cascades.
One-minute OHLC cannot validate taker arrival price, latency loss, maker queue position or fills.
Maker/hybrid routes remain SOURCE/DATA BLOCKED pending deterministic queue-aware replay and missed-fill rules.
Current fees cannot be asserted to have applied in 2024.
Venue-native history must exist for the chosen period; Binance candles are not executable prices on another venue.
Funding must use actual contract schedules/history; short holding time does not automatically eliminate funding.
A quiet-period detector needs source receipt time, watermark, completeness and outage behavior.
No new family freeze is asserted complete while these parameters and causal authority are unresolved.

## Next permitted gate
Source-only causal signal design and Lighter/other low-fee venue instrument/data availability acquisition, with no protected price reads.
A new family must specify causal decision time, source delivery latency, venue-native replay, conservative depth-based taker fills, sizing/rounding, fees, funding, missed fills and original-or-stronger sample/statistical gates.
Do not use Oct-Dec to evade V0.2 sample failures.
No new untouched period is authorized by this document.
The audit is not a global claim that all execution venues fail.
The next legitimate verdict reached is SIGNAL AUTHORITY BLOCKED, with a low-fee external lead preserved.

## Verification
Read exact run metadata, exact-head workflow and exact-head executor; compared current corrected sign function.
Synthetic sign check: prices 100→101 yield old +1%, genuine SHORT -1%.
Synthetic causal check: entry precedes cascade-end knowledge.
No market data, outcomes, PnL, protected period or exchange account accessed.

## Official sources retrieved 2026-10-01
- https://www.binance.com/en-BH/fee/futureFee (USDC promotional/overlapping rates not adopted)
- https://www.bybit.com/en/help-center/article/?id=000001584
- https://www.okx.com/en-eu/help/how-to-calculate-the-contract-transaction-fee
- https://support.kraken.com/ca/articles/360048917612-fee-schedule
- https://help.coinbase.com/en/international-exchange/trading-deposits-withdrawals/international-exchange-fees
- https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees
- https://www.bitget.direct/support/articles/12560603825829
- https://miniapp.gate.com/zh/announcements/article/50390
- https://apidocs.lighter.xyz/docs/account-types
- https://apidocs.lighter.xyz/docs/websocket-reference
- https://apidocs.lighter.xyz/reference/orderbookdetails
- https://lighter.xyz/terms

Firewall: new_market_outcomes_opened=false; oct_dec_opened=false; market_2025_opened=false; market_2026_opened=false; live_trading=false; orders=false; wallets=false; exchange_mutation=false; merge_main=false; post_outcome_tuning=false.
