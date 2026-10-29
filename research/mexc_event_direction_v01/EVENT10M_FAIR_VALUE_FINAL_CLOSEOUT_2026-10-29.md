# EVENT FUTURES FAIR VALUE LAB — FINAL V0.1 SCIENTIFIC CLOSEOUT
Date: 2026-10-29 (Europe/Zurich). User demanded full scientific attack through verifiable verdict, BTC/ETH **MEXC Event Futures** 10-minute only. Excluded NVIDIA (separate research), MU, SPCX and distinct MEXC 5/15-minute Prediction Markets.

## Scope, threat model and source authority
- Exact separately named Event Futures product (not MEXC Prediction Markets); official documentation: https://www.mexc.com/support/futures-trading/event-futures and https://www.mexc.com/learn/article/what-are-prediction-futures-/1
- Reused exact former V0.12 independently audited public Chromium GET-only snapshot collector, with no source logic changes; page naturally produced Event Futures detail response HTTP200. Fresh unauthenticated contexts; all sensitive/private routes and non-GETs blocked. Existing source read-only snapshot PASS V0.12; older October 29 15:04 UTC snapshot preserved in research PR #280, not treated as contemporaneous outcome.
- Pre-outcome freeze: EVENT10M_FAIR_VALUE_NOARB_FREEZE_V01.md, initially committed SHA 50e86225694a4a05c411402df107bfd331d9458b. Neither event-price outcomes nor trade/account actions were authorized.
- [Authoritative GitHub Actions source + math run #40930880041](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40930880041), job 123648658000, CI conclusion success, artifact event10m-fair-value-noarb-v01 ID 12921868234, immutable compressed archive digest sha256:d0aca367431c7c24a74c7e67a441966c76fb0f6cace5cdf23af649fa44e58be8. All workflow steps PASS, offline source-independent arithmetic unit checks PASS.
- Two public independent Chromium captures, 2026-10-29T18:27:21.854093Z and 2026-10-29T18:27:36.424176Z; both captured identical Event Futures product detail raw JSON SHA256 13fd5ea6a34789e8f87624d223b38409aef408396d33a0cb6ff2bb76efe3c80a. Public detail URL https://www.mexc.com/api/platform/futures/api/v1/event_contract/detail . Original evidence snapshots and normalized exact scoped report retained in artifact; NO raw market future outcomes.

## Actual observed 10m product payout data
Both snapshots:
- BTC_USDT 10m contractId=10 state=ONLINE upPayRate=0.70 downPayRate=0.70. Minimum success probability one-sided 1/1.70=58.823529% (ignoring cost).
- ETH_USDT 10m contractId=11 state=ONLINE upPayRate=0.80 downPayRate=0.80. Minimum success probability one-sided 1/1.80=55.555556% (ignoring cost).
- Both directions are symmetric at each snapshot. No payout change observed between 15-second-separated captures. This does NOT establish intraday stability or a historical payout history; product pay rates can vary.

## Exact deterministic no-arbitrage test
Winning Event Futures trade returns principal plus profit equal to principal times payout. Losing trade loses principal; tie returns principal. The rates are net PROFIT multiples, **NOT** market-implied probability quotes. The two strict directions are complementary if the compared expiry/target are identical.

Write A=1+qUp and B=1+qDown. Divide one total stake into wUp=B/(A+B), wDown=A/(A+B). The normalized return in either strictly UP or strictly DOWN settlement is AB/(A+B). Net guaranteed conditional on non-tie is AB/(A+B)-1 and synthetic implied state price sum is 1/A+1/B. Static two-sided arbitrage requires this sum <1 or net >0:
- BTC q=0.7/0.7: wUp=wDown=0.5. Synthetic sum 1.176470588; net = -0.15 of combined stake (e.g. 10+10 USDT -> 17 USDT payout whichever side wins, loss 3 USDT).
- ETH q=0.8/0.8: wUp=wDown=0.5. Synthetic sum 1.111111111; net = -0.10 of combined stake (10+10 USDT -> 18 USDT payout, loss 2 USDT).
- Tie, if both sides receive their own principal as documented, returns total stake and cannot create positive arbitrage.
- Eligibility of simultaneous opposite-side positions, any fees, actual simultaneous payout locks and exact server entry/settlement price parity are **NOT** verified. These unknowns cannot rescue negative pre-cost static math at captured payout rates. No riskless combination was identified in either observed snapshot.
- Observations are sparse: TWO quotes ~15 seconds apart; do NOT declare that an arb can never exist in a future altered payout. Fail closed to observed scope.

## Directional "mispricing" epistemic gate
Without independently calibrated pre-outcome probability p=P(UP), no empirical expected value can be computed from pay rates alone. Deterministic conditional formulas EV_UP=p*qUp-(1-p) and EV_DOWN=(1-p)*qDown-p are NOT measured EV. Payout is risk/volatility-dependent per MEXC; q is not a displayed market-derived probability. No as-of verified model p, no contemporary actual Event Futures executed openPrice/expiry, and no validated actual fees. Earlier event-direction model gate PR #275 is MODEL_NOT_FROZEN/SOURCE_GATE_REQUIRED; no reason to duplicate or resurrect closed historical strategies. Historical index-proxy results PRs #277/#281/#282 and MU #287 cannot be relabeled actual-product fair value.

## Practical execution caveat (official documentation)
MEXC Event Futures FAQ 3.7 explicitly says Event Futures currently do **NOT** support API trading. Positions also cannot be closed before expiry (FAQ 3.4); exact payout fixed at order submission (FAQ 3.2). Consequently no supported automated trading GO from this study. Public APIs/market data collectors support read-only research, NOT Event Futures order execution.

## FINAL DECISION
**SOURCE_CURRENT_PASS / 2 OBSERVATIONS / MATH_PASS / NO_STATIC_TWO_SIDED_ARBITRAGE_AT_SAMPLED_QUOTES / NO_INDEPENDENT_DIRECTIONAL_FAIR_VALUE_EDGE / NO_LIVE_GO.**

Close this static arbitrage family at the observed quotes. Do not repeat identical public checks as if they were independent discovery; do not retune historical date/fee/odds assumptions. Future NEW separate prospective probability-calibration effort only after independent model freeze, source time custody, actual price/settlement correspondence, exact payouts and real delivery/available execution semantics. The lab remains a valuable *veto filter* for false positive economic claims, not a profit engine.

No trades, accounts, private endpoints, login, keys, wallets, spending, protected September holdout, NVIDIA duplication, merge or modifications to main. Workflow is push-only on isolated branch and does not run on main.
