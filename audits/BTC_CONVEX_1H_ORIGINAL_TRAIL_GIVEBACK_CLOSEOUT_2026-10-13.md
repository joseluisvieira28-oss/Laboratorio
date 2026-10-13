# BTC-CONVEX 1H — ORIGINAL V5 TRAILING: GIVEBACK, DEACTIVATION, EXIT PATH AUDIT
**2026-10-13 UTC — research only.**
Freeze prior to path outcome: `research/btc_convex_1h_protection_20261013/PATH_AUDIT_FREEZE.md`, commit `db36e581b6ae334aaa681d001c37510ce15883cb`.
Base model: immutable completed original 1h historical 2021–25 engine artifact 38426153613 / 11828479302 (BTC-CONVEX V5 5m canonical V02).
Verification run: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38428476711 **SUCCESS**; five synthetic invariants PASS, exact 1h BASE 77/77 and 1h STRESS 78/78 historic first-stop exit times/reasons/price parity PASS.
Economic and MFE artifact https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38428476711/artifacts/11828849111.
Source: original official public Binance USD-M BTCUSDT 5m, January 2021–December 2025, 60 monthly data files; every archive passed both publisher .CHECKSUM and independent SHA256 equality against original prior V02 source manifest. No 2026 protected holdout. MFE uses 5m high only strictly before stop candle (intra-candle ordering unknown); not tradable executable bid.

## Factual observed original V5 stop behavior
| Original 1h V5 2021–25 | BASE | STRESS |
|---|---:|---:|
| Exact closed exit paths reconstructed | 77 | 78 |
| Closed trades with any 1h-close +5% trailing activation | **27** | 27 |
| Activated trailing at least once, but eventually closed at net loss | **10** | 10 |
| Trades where trailing later deactivated at least once (close below +5%) | **22** | 22 |
| Total transitions activated→inactive | **155** | 148 |
| Trades where reset ACTUALLY WEAKENED the protective stop above initial | **9** | 9 |
| Actual protective-stop weakening events | **72** | 72 |
| Trades that ever had a protective trailing stop strictly above initial | **22** | 22 |
| MFE over +10% then closed with net loss | **4** | 4 |
| Median potential high-to-exit giveback (all trades) | **6.7115 pp** | 6.7095 pp |
| Median potential high-to-exit giveback (17 winning trades) | **16.0561 pp** | 16.0866 pp |
| Largest potential high-to-exit giveback | **21.4496 pp** | 21.4902 pp |
| Mean 5m-high MFE proxy across closed trades | **11.0769%** | 10.9226% |

Important: **155 reset events are NOT 155 avoidable losses or stops altered**. Only 72 such BASE events across nine trades caused the next protective stop to actually weaken. Many +5% activations happened when 12%-from-peak trail was still BELOW the fixed initial stop, causing no protective upgrade.
**Counterfactual not measured**: removing resets/sticking protection could alter exit timing, future entries, funding accrual, competition for a slot, and most importantly destroy 2024 rare right-tail winners; do not convert giveback MFE into savable PnL. The original nonlatched V5 exit itself is mechanically authentic in the exact same historical source.

## Top 3 original net winners (all exit year 2024)
- Highest winner BASE **+1,134.1032 USDT**, MFE proxy +74.8717%, slip-adjusted exit +53.8563% from entry price, proxy giveback **21.0154 percentage points**; 16 deactivation events, 9 stop-weakening events, 110+ days holding exposure.
- Second BASE **+993.5341 USDT**, MFE +73.7839%, exit +52.8992%, giveback **20.8847 pp**; 5 activation resets but ZERO actual protective-stop weakening events.
- Third BASE **+967.7878 USDT**, MFE +65.8121%, exit +45.8854%, giveback **19.9266 pp**, zero deactivations and zero weakening.
These winner exits are not a mechanical proof of failure: with a trail 12% below a price peak, a 20 percentage-point gain giveback from high price appreciation can be entirely consistent with the frozen design. A tighter trailing stop would need matched OOS causal testing and could cut these winners very early.

## Relationship to verified fee/funding study
See `audits/BTC_CONVEX_1H_COST_FUNDING_TAIL_FORENSICS_2026-10-13.md` in this same branch:
- BASE closed price-only (after modeled slip) +2,954.116754 USDT; closed fees -276.379212; closed funding -1,150.590528; closed net +1,527.147014.
- Funding is 4.16× fees within the same 77 original closed trades; longest closed hold 110 days, median 3.22 days.
- The top 3 2024 winners sum +3,095.425 USDT and dominate historical gross positive payouts; eliminating those on unchanged ledger leaves negative -1,568.278 USDT.
- A strategy promising smaller givebacks without verified unchanged tail economics is not an upgrade; unrealized high-price MFE is not a realizable fill.

## Next allocation / scientifically legitimate continuation
1. **Do NOT retune Parent activation (+5%), initial stop (-4%) or trailing 12% from BTC 2021–25.** It would be hindsight selection, not a new discovery.
2. Cross-check the previously frozen H1 sticky-trail closeout in the repository. The sticky child is not automatically new and should not be readmitted after prior unfavorable untouched evidence.
3. Treat public historical funding-rate + canonical 5m-market-open settlement price as model-dependent. Require exact per-timestamp official mark/funding parity and independent venue/fee evidence; fee rebates/maker queues not assumed.
4. Prospective side-by-side testing requires signed/append-only postfreeze event receipts and a matched identical-position-exposure Parent and new candidate; none is deployed by this study. No automatic trade authority.

**VERDICT: ORIGINAL TRAIL PATH VERIFIED / DEACTIVATION REAL BUT PROTECTIVE WEAKENING CONCENTRATED / FUNDING FIRST-ORDER / TAIL FRAGILITY REMAINS / NO FREE PROFIT / NO MICRO-LIVE GO.**
