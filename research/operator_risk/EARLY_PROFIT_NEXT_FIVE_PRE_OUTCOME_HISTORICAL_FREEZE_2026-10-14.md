# EARLY-PROFIT NEXT FIVE — PRE-CHILD-HISTORICAL-OUTCOME FREEZE
UTC date 2026-10-14. Explicit user direction: preserve ORIGINAL SOL-CONVEX 1H and BNB-CONVEX 4H, test the other recommended candidates with risk management, show the results.

## Scope and fixed ordered candidate set (no selection after new child outcomes)
1. SOLUSDT native 5m CONVEX V5 — 2023–25 published parent BASE ≈+59.99%, STRESS ≈+57.77%, 182 closed.
2. SOLUSDT 4h V5 — parent BASE ≈+35.90%, STRESS ≈+35.42%, 44 closed.
3. BNBUSDT 30m V5 — parent BASE ≈+19.67%, STRESS ≈+18.17%, 51 closed.
4. ETHUSDT 1h V5 — parent BASE ≈+18.77%, STRESS ≈+18.34%, 47 closed.
5. DOGEUSDT 4h V5 — parent BASE ≈+15.66%, STRESS ≈+15.26%, 44 closed.
These published approximate baselines were seen in PR #215 / #217 before this experiment. Parent must reproduce exact native V5 original for all five; failure FAIL CLOSED. No 2026 outcomes opened, no new independent OOS; this is a historical diagnostic, not trading alpha validation.

## Immutable parent + sources
- Original 2023–25 common 8-alt indicator and simulated fills from immutable SHA `42d6748864dd78b911b5f1fc775ff1950b556d2b` under `research/convex_8alt_common_2023_25/common_3yr.py`, original V5 `base.simulate` and `src.load_parent`. Native 5m parent use original `old.base.simulate(300000, five_bars,five, funding, slip)` same as PR #217 original native 5m study; native 5m is an explicitly different 5m timeframe, **not** a 5m execution proxy for 1h signal.
- Official Binance Vision public USD-M futures 5m prices 2022-11 through 2025-12 and 1h independent source same period, funding official archive 2023–25. Per symbol exactly 333,216 5m price bars; 27,768 1h bars; 3,288 funding records, publisher SHA256 ZIP checksums. Continuous UTC, fail closed on missing source. Only 2023–25 outcomes plus prior source warm-up.
- All Parent signals and entry scheduling, stopped trades, fees and funding unchanged. Original nonlatched trailing can loosen; preserved in Parent comparator only. Start 10,000 USDT paper equity, 20% notional LONG 1x, initial stop -4%, trailing 12% of peak when fully closed signal bar >=+5% above entry. One slot per portfolio. BASE 8bps taker+2bps slip **per side**, STRESS 8bps+5bps per side, signed observed actual funding rate with 5m market OPEN price proxy (not true liquidation mark), no zero-cost rescue.

## Fixed child risk management — exact same as previous 2026-10-14 historical SOL1h/BNB4h tests
- 1R_price equals original executed LONG entry minus initial -4% stop, NOT leverage ROI. Only after *completed 5m candle close* witnesses +1R_price, attempt to sell 50% at NEXT 5m OPEN at adverse slip/fee if pro rata fully priced estimated NET realized cash from half >= 0.25 original complete modeled R_cash; initial R_cash is full original price stop distance with adverse stop slippage, both fees, 5bps funding reserve.
- Then position remainder uses unchanged original stop through same 5m bar, later at completed 5m close request conservative net (fees, original allocated fee, signed funding) break-even and a **monotonic stop**; in any later completed TF bar LONG stop never decreases even when Parent nonlatched resets. If a proposed BE stop would already be crossed at prior close, DO NOT retroactively sell at it; sell next 5m OPEN if still eligible with adverse fill. Stops take precedence over pending half on open gap; within-bar stop-first conservative, no filling at past candle highs. Sizing/reentries recomputed on evolving cash, no static ledger subtraction.
- 50% fractional position split is hypothetical; min contracts, actual executable BBO, stop ACK, liquidation and maker queue not proven. Still simulation and no guarantee capital maximum loss in outage or gap. Historical child must NOT mutate parent.
- These five child outcomes MUST be all reported even if negative and even if positive. Report BASE, STRESS cumulative terminal marked and closed cash separately, parent parity, closed count, partials, PF, max 5m bar-low drawdown, top3 static concentration, funding/fees, year cash, source SHA hashes. No outcome-driven +0.5/1.5/2R or fraction optimization in this historical sample.

## BNB Launchpool and liquidation → SOL SHORT next-stage feasibility
- Both are different causal families, not V5 clones. BNB Launchpool parent existing 66 event historical ledger positive, but no immutable original *initial invalidation STOP* or tick-level intra-event executable path identified in canonical evidence. BTC liquidation->SOL SHORT holdout n35 +9.07bps after a flat hurdle, similarly lacks a frozen original stop. **No fabricated 1R**, no historical price-return fitted stop; conduct source/stop audit only, and label STOP_SOURCE_NOT_DEFINED until a scientifically defensible pre-outcome stop and price tape are available.

## Standing governance
Historical research-only, isolated branch, draft PR, NO merge main, no authenticated exchange requests/accounts/wallet/order mutation, no live trading, no Render or Windows deployment, no spending, no 2026 protected holdout or retroactive live authority. This freeze and commit must precede the new child market outcome replay.
