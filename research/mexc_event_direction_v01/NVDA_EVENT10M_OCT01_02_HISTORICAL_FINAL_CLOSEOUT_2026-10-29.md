# NVIDIA CASH → MEXC EVENT-10M: OCTOBER 1–2 FROZEN HISTORICAL REPLAY CLOSEOUT
Date: 29 October 2026 | DISCOVERY ONLY | NO ACCOUNT, ORDERS, CAPITAL, OR PROTECTED HOLDOUT.

## Scientific verdict
**ONE PROXY WIN OUT OF ONE QUALIFIED SIGNAL / 23 ABSTENTIONS / NO CERTIFIED ECONOMIC EDGE / NO LIVE GO.**

Frozen V0.1 NVIDIA cash-reference rule preserved without retuning:
- Only **2026-10-01 and 2026-10-02**, 12 precommitted 10-minute decision slots each day, NY-local 09:35–11:25.
- Features: NVDA cash 1-minute close(t-4)→close(t-1) 3-minute impulse, MEXC NVIDIA_USDT standard-futures INDEX likewise. Qualify if `abs(cash_bps)>=10`, `abs(cash_bps-index_bps)>=5`, `cash_bps*(cash_bps-index_bps)>0`; direction=sign cash; else ABSTAIN.
- Historical decision **t+10s**, expiry **t+10m+10s**, but the only available historical return proxy was MEXC **1-minute INDEX OPEN(t)→OPEN(t+10m)**: **both** source proxy prices are from 10 seconds before the stated decision/expiry; the exact event order openPrice and Event Futures settlement price at t+10s are **unknown**.
- q=0.80 hypothetical symmetric WIN payoff (0.85 sensitivity only), not verified historical Event Futures payout on Oct1–2; no transaction, account, order, real Event Futures PnL, as-of cash equity receipt or market executeability established.

## Source and audit sequence (no hidden failures)
1. Source-only [run 40930443134](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40930443134), commit 54bb0766a5444db3ebc046ad385dc7015e5f45b9, verified ALL required Yahoo cash & MEXC index minute starts with SHA256 raw receipts. No win/loss computed.
2. First historical attempt [run 40930889735](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40930889735) passed 7/7 synthetic tests but **BLOCKED BEFORE ANY OUTCOME** due changed full Yahoo JSON body SHA256. Do not mistake this for a negative signal result.
3. Separate pre-outcome canonical source freeze: [run 40931140788](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40931140788), commit 2cb741a4e7604d86bbeea363a453ba2f5aac6673, TWO independent GETs per provider; required precise 1m feature/entry/expiry time+price bars had **matching canonical SHA256** although Yahoo entire JSON metadata changed. Hashes frozen BEFORE directional outcomes.
4. Actual historical replay [run 40931342256](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40931342256), commit 68eaa5f39c871f64cf5d241f0a3e642a71fad9c5, 7/7 synthetic parity tests, source canonical SHAs verified, all 24 original slots reported, no missing bar substitutions. Artifact **12921544371**, ZIP sha256 `531c9d88a23e4222950bd2622dc2380566a8f75629611f97cc2e1fde666f1a89`, member `historical_proxy_report.json` includes all 24 observations, raw source hashes and all baselines.
5. Independent local audit of the emitted ZIP: 24 unique scheduled times, exactly 600000ms decision-to-expiry, recomputed every `abs(cash)>=10, abs(gap)>=5, cash*gap>0` signal, direction/outcomes and four baseline payout arithmetic cells; **all PASS**. Audit does NOT independently reconstruct historical exchange ticks, since those are unavailable.

## The one selected forecast (historical proxy, NOT executed)
- **2026-10-01 at 09:45:10 America/New_York / 13:45:10 UTC**, expiry target 09:55:10 EDT / 13:55:10 UTC.
- Predecision NVDA cash impulse +**42.58166414** bps, MEXC NVIDIA_USDT index impulse +**34.72071525** bps, positive cash-minus-index gap +**7.86094889** bps. Frozen candidate = **UP**.
- MEXC standard-futures INDEX 1-minute OPEN 09:45 = **231.21**, 09:55 = **231.72**; positive ten-minute *minute-boundary proxy* movement. Outcome proxy **WIN**. Direction and proxy payoff do NOT prove the MEXC Event Futures actual contract would have settled UP at +0.8.

## Full results (hypothetical fixed q=0.80)
| Diagnostic | Signals / slots | W / L / Tie | Accuracy ex ties | Unit EV q=0.80 |
|---|---:|---:|---:|---:|
| Frozen cash-lag candidate, 2 days | **1 / 24** | **1 / 0 / 0** | **100% (n=1)** | **+0.80** |
| Candidate 2026-10-01 | 1/12 | 1/0/0 | 100% (n=1) | +0.80 |
| Candidate 2026-10-02 | 0/12 | 0/0/0 | N/A | N/A |
| Cash-only impulse >=10bps across 24 slots (predeclared comparator) | 15/24 | **9/6/0** | **60%** | **+0.08** |
| Cash-only first day | 7/12 | 5/2/0 | 71.43% | +0.28571 |
| Cash-only second day | 8/12 | 4/4/0 | 50% | -0.10 |
| Always UP, all 24 | 24/24 | 11/13/0 | 45.83% | -0.175 |
| Always DOWN, all 24 | 24/24 | 13/11/0 | 54.17% | -0.025 |
| Always UP on **the same single candidate slot** | 1/1 | 1/0/0 | 100% | +0.80 |
| Cash-only on **the same single candidate slot** | 1/1 | 1/0/0 | 100% | +0.80 |

The one candidate **would also win with always-UP or cash-only on the same slot**; with n=1, the additional lag filter has demonstrated **no independent incremental predictive value**. Ex-post choosing the cash-only variant (9/15, +8% simulated) after seeing these outcomes would constitute model selection, NOT predeclared evidence of a new profitable strategy.

## Hard limitations and next gate
- Break-even for q0.80 hypothetical and no costs is >55.56% win rate, but n=1 selected signal cannot substantiate that threshold. The frozen forward gate needs at least 60 qualified resolved signals on >=15 distinct sessions; here **one** qualifying signal on **one** day. Observed selectivity 1/24 =4.17% is not proof of economically viable opportunity frequency.
- Original full Yahoo response body changed; canonical required prices were repeatable in the two source probes. This confirms local reproducibility, not their contemporaneous availability on Oct 1–2; the Yahoo public feed is not certified as-of NBBO.
- Standard MEXC INDEX OPEN proxy is 10 seconds BEFORE the hypothetical Event Futures decision and expiry ticks. Server-assigned contract `openPrice` and precise expiry price were NOT available or verified; payout at Oct1–2 is NOT known. No actual trade economics.
- Only two **previously exposed discovery dates**; the NVIDIA Oct05–30 sealed forward and September 2026 protected holdout remain CLOSED. Do not use those dates for opportunistic retrospective rescue; no new best threshold/session from this result.
- November 2–30 paper V0.1 freeze remains UNCHANGED. The V0.7 GitHub server-side artifact custodian is prepared but dormant on research branch; no automatic paper collection scheduled or activated, no default-branch/main changes.

**Scientific decision: maintain hypothesis as UNPROVEN, not a validated diamond. No tuning. Next legitimate test = prospectively signed 10m decisions with exact market as-of and independent index/event settlement parity, after the old forward period is legitimately closed.**
