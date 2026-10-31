# CRYPTO LAB — BTC Event Futures 10m: ADVERSARIAL INDEPENDENT FINAL OPERATIONAL VERDICT
Date: **2026-10-31**. Scope: precisely one previously frozen BTC-only hypothesis (OKX Spot top5 order-book notional imbalance vs opposite MEXC perp book imbalance). No other model activation or extension.

## Executive answer
**PUBLIC_SOURCE_AND_RAW_SEMANTICS_INDEPENDENTLY_REPLAYED_PASS**
**FUTURE_PROSPECTIVE_PAPER_ONE_SHOT_DORMANT**
**ZERO_PREOUTCOME_REAL_SIGNALS**
**ZERO_INDEPENDENT_REAL_10MIN_OUTCOMES**
**REAL_EVENT_FUTURES_OPEN_AND_SETTLEMENT_INDEX_PARITY_UNCERTIFIED**
**ECONOMIC_EDGE_NOT_TESTED / NO LIVE GO / NO AUTOMATED PROFITS**

This is a definitive **operational/source** closeout at 2026-10-31, NOT a final economic edge determination. The frozen prospective period Nov 01–30 has not started. Do not claim "edge rejected" on zero samples. Do not infer profitability from code PASS or 70% payout.

## Adversarial defects actually found and corrected
1. **HIGH SCIENTIFIC INTEGRITY**: V0.5 GitHub custodian checked receipt-declared source SHA256 and 8 file bytes, but did NOT independently derive book imbalance, dynamic Event Futures payout, index price and source timestamp from the original HTTP JSON. A self-inconsistent receipt would remain accepted. V0.6 `btc_event10m_raw_replay_v06.py` independently reparses each raw OKX/MEXC book snapshot, recomputes top5 notional bid/ask imbalance/spread and notional values, verifies 3 order book identities/order, dynamic MEXC exact BTC 10m contractId/state/up/down payment and MEXC index price/server timestamp. Integrated into `verify_archive` before issuing custody PASS. Deliberate tampering of imbalance, payout, price, timestamp and contract state is now rejected.
2. **HIGH WORKFLOW CONFIG**: V0.5 dormant GitHub Actions blueprint literally contained **five escaped GitHub expressions**. Removed extra backslashes, tested precise token/expression presence. Prior configuration could have passed malformed GitHub token and artifact id values to the independent verifier.
3. **HIGH SOURCE CAUSAL FRESHNESS**: V0.5 used HTTP receipt freshness for MEXC orderbook without asserting that the *book's actual exchange timestamp* is itself fresh. Source-only 3-GET real probe [#41227731635](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41227731635) proved public MEXC BTC depth **server timestamps exist and are valid**, ages **365ms, 195ms, 363ms**, all raw hashes recorded, 20 bids+20 asks each. The V0.6 source gate is now **fail-closed** for absent/future/stale MEXC depth timestamp beyond 2sec, verified again against archived raw bytes. This is a stronger reliability check, NOT a new trading threshold or after-outcome selection.
4. **Not fixed / must block financial GO**: no independent public official parity of actual Event Futures server-assigned entry/open index price, exact 10minute expiration index and MEXC standard futures index used for shadow diagnostic. [Official MEXC rules](https://www.mexc.com/support/article/how-to-use-event-futures-on-mexc-a-simple-and-accessible-futures-trading-method-395277582692768768) say expiry uses underlying index but do not supply sufficient ticker-specific server tick parity evidence. Index proxy result would NOT be a real Event Futures fill, tradable signal or realized PnL. HTTPS transport of the raw HTTP bodies is not cryptographically attested independently by GitHub; GitHub attests archival bytes/time, not exchange causality or front-running performance. Visible book depth is cancelable, not executed trade flow.

## Independent new evidence — ZERO history opened
- Frozen original source-only test 2026-10-30 [#41096454537](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41096454537), artefact ID **12996537229**, GitHub server zip SHA **a49052bce9e0ce8d7ba216bfcc00a5b9ca9ff5d474a06c591398b5553d1b567d**: BTC_USDT Event 10m contract 10 ONLINE, observed payout **qUP = qDOWN = 0.70**, public index 77199.4, 3 OKX + 3 MEXC depth book receipts; all four same-moment causal source gates previously passed. **No direction generated**.
- [V0.6 adversarial semantic code tests #41227639211](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41227639211): **11/11 PASS**, plus dormant workflow token expression guard. All synthetic.
- [MEXC book clock source #41227731635](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41227731635) genuine 3 valid distinct REST responses, exchange timestamp age 365/195/363ms.
- [V0.6 strengthened source + raw tests #41227892904](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41227892904): **8/8 strict clock guards + 11/11 independent raw semantic tests PASS**, no market outcomes. Previous #41227808566 failed one stale-source synthetic assertion because stricter gate now raises ValueError (correct behavior); fixture expectation repaired.
- Most important new **independent REAL SOURCE REPLAY** [#41228044136](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41228044136): GitHub runner downloaded original Oct30 source archive by exact previously declared artifact ID and pinned server zip SHA256, checked **all 8 exact HTTP raw SHA256 and independently reconstructed price-side book, original BTC Event q=.70, server timestamps and standard index**. Status **ORIGINAL_SOURCE_RAW_SEMANTICS_AND_EXCHANGE_CLOCK_PASS** with all 4 stricter source gates PASS. This proves the originally archived source data is internally reproducible under the new verifier, not just mock data.

## Frozen scientific hypothesis and dynamic payout
BTC only, UTC 10m slots Nov1–30 inclusive; exactly three 4–8 sec-apart pairs in which OKX Spot BTC/USDT top5 imbalance has magnitude >=0.25 in one direction and MEXC perp BTC_USDT top5 imbalance >=0.25 in the **opposite** direction, across ALL THREE. Follow OKX side; else ABSTAIN. Every book, payout and index tick must be observed before immutable decision with frozen as-of gates (source last 2s, product q 10s), no after-result tuning. Oct30 q=.70 implies break-even p > 1/1.70=**58.82%** non-tie BEFORE any additional costs. At p=.50 and q=.70, EV=(.5*.70)-(.5*1)=**−0.15 per stake unit**. Payout changes, so never assume .70 in November.

## Why today's "final" cannot be economic
- The proper **November 2026 prospective period has not begun** as of Oct31 and the current proof contains **0 real candidates** and **0 resolved forward Event Futures bets**. No 10min win rate, Bayesian EV or Sharpe can be computed.
- Frozen min >=300 qualified independently resolved non-tie events on >=20 different UTC calendar days plus independent untouched chronological last third, block bootstrap confidence lower bound >0 after costs and multiplicity. No meaningful signalled frequency estimate exists.
- Even if samples resolve as *public INDEX shadow only*, no Event Futures real executed entry or expiry price parity proof, so **no certified net economic edge** may be granted.
- `.github/workflows/btc-event10m-paper-one-shot-dormant-v05.yml` is **DORMANT** on a research branch: GitHub workflow_dispatch requires default-branch registration. No scheduler, runtime executor or real Nov 10-minute collector has been activated. Nothing can be collected in the future just because code exists. No authorized main merge, so this was not modified.
- No accounts, capital, orders, login, private endpoints, wallets, paid data, main changes or protected Sep/NVIDIA Oct5–30 outcome reads.

## Decision and next binding dependency
**Technical gate: GO for a properly authorized FUTURE-ONLY paper pilot once an actual runner is activated.**
**Economic gate: NO LIVE GO and EDGE UNTESTED today.**
Before promoting: activate a compliant read-only prospective runner without violating main restriction (or obtain separately authorized operational registration), record every attempted UTC 10m slot including blockers and ABSTAIN, upload original source+decision bytes before first expiry, verify GitHub server custody and event contract's exact settlement authority, collect legitimate 300/20 forward samples and then run frozen economic tests. No shortcut to economic FINAL VERDICT. Any request to claim final profitability before these events is impossible to prove honestly.

**End of V0.6 independent adversarial attack: TRUE operational advances, ZERO made-up trading success.**
