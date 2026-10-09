# CRYPTO LAB — ASYMMETRIC PAYOFF: SCIENTIFIC NEXT-TEST CONTRACT
Date: 2026-10-09
Status: DESIGN / NOT ACTIVATED / NOT A NEW FORWARD FREEZE.
Authority: research only; cannot start new prospective scoring until a fresh, separate pre-outcome activation freeze records software SHA, exact first eligible future boundary, source contract, frozen costs and deterministic validations.

## Priority A — BTC-CONVEX V0.2: finish existing, do not redesign
- The Parent V5 1h long-only BTC/ETH/SOL/BNB rule and the V0.2 freeze dated Sep24 remain EXACTLY intact. No reweighting of symbols or promotion based on historical ETH/SOL/BNB results.
- Current inspected JSON snapshot time 2026-10-07T23:31:25.776571Z: 1 resolved ETH loss, 3 open; Checkpoint A 10, B 25, C 50 not met.
- Validate the following at EVERY newly observed native immutable artifact: authority SHA, source/funding availability, 1h bars fully closed, next-bar causal entry, no pre-boundary trade, one position per symbol, non-latched trail semantics unchanged, immutable trade identity, funding and two-sided fees/slippage, no duplicate same-bar fill; hashes/receipt times retained.
- Checkpoint A 10: integrity only; B 25: distribution/fragility diagnostic; C >=50, >=3/4 assets with >=5 closed: formal V3 adjudication including 2026 true forward NET expectation, PF, bootstrap uncertainty, largest winner removal, time concentration, observed MTM DD, min-notional and practical capital-size feasibility. No automatic trading authority.
- Historical wins do NOT overcome 2026 negative evidence, severe account drawdown, failed independent second basket, or changing funding conditions. If source/replay irreparably invalid, STOP instead of filling historical holes.

## Priority B — TFG broad-bull Donchian12H: STOP old epoch, only new scientific epoch
Original current deployment failed its *execution integrity* gate:
7 same-symbol overlap violations; purported fills timestamped 15.4–98.3 minutes before decision receipt; 10 raw -1R outcomes. These are not 10 independently clean trials.
Old signals/resolutions and freezes are APPEND-ONLY, retained and excluded from all future confirmation samples. Do not relabel a failed implementation as valid NO_EDGE for the faithful strategy.

### Proposed future research V2 execution contract (not activated; NO performance claim)
**Economic question:** Can a 12H Donchian breakout conditional on independently defined broad-bull participation capture 3R moves after *observable* entry/exit liquidity and realistic costs?

Preserve original signal discovery only as a candidate (long-only; six frozen spot symbols BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT; 40 complete 12H high breakout; ATR28; signal-low -0.25 ATR28 stop; target gross 3R; max holding 80 complete 12H bars; BTC previous fully closed UTC daily >SMA200; SMA200 rising vs 20 complete days prior; >=4/6 closed daily prices > own SMA100; missing source -> no signal). NO threshold optimization against known 2026 losses.

**The new experiment's material change:** replace unobservable `next 12H open` with a *precommitted and market-observable* paper execution. A deterministic 10-minute-after-close decision evaluation is admissible ONLY if the signal, source and quote arrive in time, as proved by separate append-only timestamps. A quote observed before the decision is NEVER executable proof. The precise polling cadence, max quote age, spread/slippage policy and entry windows MUST be frozen in the activation commit, not chosen after seeing the first quotes/outcomes. Skip with an explicit `NO_ACTION_MISSING_SOURCE` receipt if any deadline/source requirement fails; no synthetic backfill.

**Execution invariants:**
1. `fully_closed_12h_signal_end <= decision_computed_at <= decision_receipt_persisted_at <= quoted_at <= paper_fill_at`; timestamps UTC, source offsets verified. Historical candle OPEN is forbidden as quote substitute.
2. Quote must be side-correct: paper BUY at contemporaneous ASK plus stressed adverse fill allowance; paper SELL at contemporaneous BID minus stressed allowance; fees funding and spread all explicit; zero fee is forbidden unless legally applicable and independently evidenced. Stress cannot be cheaper than base.
3. Capture the order-book depth sufficient for all precommitted small capital test sizes; mark trades non-executable when min-notional, min-qty, precision or depth fails. Include position sizing at <=0.25% of hypothetical account equity risk per position and <=1% aggregate planned initial stop risk; no leverage rescue. These risk limits are hypotheses for an entirely new child, not changes to original V1.
4. Persist full UTC source, source-provider, exact raw response digest, exchange ticker/order book timestamp, fetched_at, decision time, receipt time, fill time, quote age, signal values, entry/stop/target, notional, top-of-book and depth, fee version, detected gaps, and rejection reasons; durable one-writer ledger. Replay cannot create a contemporaneous receipt retroactively.
5. One open position per symbol; suppress later signal until actual prior exit is durably recorded. Exit by first *observed after-trigger* executable bid and conservative stop-first rule when path ambiguous; delayed fills/gaps may lose more than -1R and must remain in sample. Never truncate those losses to a 1R cosmetic display.
6. Zero silent missed eligible signals, duplicate trades, unresolved/unknown execution paths at final gate; failure produces `EXECUTION_INTEGRITY_FAIL` separately from `NO_EDGE`.
7. No account access, private trading endpoints, orders, Render deployment, capital spend, or main merge.

### Before any fresh outcomes: mandatory activation conditions
- Public source transport accessible from the ACTUAL collector environment, with continuous completed 15m archive and exact daily regime warm-up for every symbol.
- Tests: delayed response, stale bid/ask, long network pause, missing 15m component, 12H boundary drift, 15m overlap, restart, double invocation, duplicate key, single-writer ownership, active same-symbol position, stop/target same tick, stop price gapping through, zero depth, min-notional infeasibility. Every failure must be fail-closed; run regression CI on code SHA.
- Separate V2 activation freeze and digest created BEFORE first scored event; first admissible future boundary is strictly later than freeze AND actual collection-on start. Do not import post-Sep16 old signals.
- Freeze minimum independent signal clusters, test horizon and OOS evidence gates up front. Proposed (NOT authorized until activation): minimum 100 resolved causally documented trades, >=12 independent UTC weeks, >=4 symbols each >=10, bootstrap by trading day/regime with lower 95% NET expectancy >0 in base, stress NET expectancy >0 and PF>1, after removal of largest winner still NET positive, no unseen costs, executable at smallest declared notional, no cross-account hypothetical hidden netting. At end if insufficient independent samples: `FORWARD_INSUFFICIENT`, not positive promotion and not permanent `NO_EDGE`.
- Hypothesis falsified for the declared capital/venue/execution route if the frozen, source-valid sample fails its preregistered net economic gates. NEVER tune cost or stop post-outcome to rescue.

## Scientific priorities and stopping policy
Priority 1: Preserve the existing forward BTC-CONVEX sample while waiting for valid resolved trades; a small historical surviving basket does not establish a small-capital income machine.
Priority 2: TFG old epoch receives NO extra trading/promotion credit. Only consider expensive V2 execution work after confirming it offers a genuine new clean forward experiment and the collector can actually preserve contemporaneous evidence.
Priority 3: No new simplistic EMA, Donchian timeframe, or arbitrary RR optimization off the already opened 2026 evidence.
Any GO requires *independent NET profit after realistic execution costs AND a feasible risk/capital envelope*, plus a separate explicit user authority for any real trade.
