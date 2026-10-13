# OPTIONS V2.1 — 10x Futures final execution go/no-go, 13 October 2026

**Verdict: LIVE 10X NO-GO. This is the end-of-audit verdict for the current MEXC BTC_USDT MARKET/MARKET execution fork, not a claim that every future 10x idea is impossible.**

### Authority and scope
Operator requested: automatic BTC Futures LONG and SHORT at 10x isolated leverage; 10 USDT **nominal** per position maximum preserved from prospective freeze. Explicit operator appetite for risk was noted, but readiness gates are factual requirements, not discretionary authorization. No order sent, no private account access, no workstation changes, no main merge.

Source branch: `experiment/options-v21-10x-protected-prospective-2026-10-13`  
Final audit branch: `audit/options-v21-10x-final-truth-gate-2026-10-13`  
Audit CI: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38386881613

### Scientific/economic decision: taker/taker route

Historical independent 2025 OOS summary in `receipts/OPTIONS_SPOTPERP_001_V21_EXECUTION_ECONOMICS_FINAL_CANONICAL_2026-09-28.json`:
- BASE10 net mean = +5.0427663334 bps/opportunity
- STRESS20 net mean = -4.6759378383 bps/opportunity
- Implied average executed weight = 0.97187041717
- Implied historical break-even full-notional cost = **15.188722945270918 bps**
- MEXC API Futures officially announced **8bps taker per fill** effective June 1, 2026, i.e. **16bps fee-only round trip** for MARKET/MARKET
- Historical OOS **sensitivity** at 16bps = **-0.78845616962 bps/opportunity**, prior to spread, slippage, funding. This is not a realized 10x Futures performance estimate.
- 10x leverage changes required margin, liquidation/risk and return on margin but **does not reduce fees per traded notional or turn a negative bps edge positive**.
- Venue minimum contract size and current equity have NOT been certified here. The cap is 10 USDT notional, not 10 USDT initial margin; both can block exposure.
- The historical OOS results from a parent spot instrument cannot promote a new stopped 10x perpetual fork: funding, basis and forced stops change outcome.

Official sources:
- https://www.mexc.com/en-GB/announcements/article/updates-to-api-futures-trading-fees-jun-1-2026-17827791535742
- https://www.mexc.com/api-docs/futures/account-and-trading-endpoints/place-order
- https://www.mexc.co/api-docs/futures/account-and-trading-endpoints/place-tpsl-order-by-position

### Engineering decision

Original 1x Windows package is installed, `Task Disabled`, `ARMED False` per last operator report; it is NOT a 10x live executable. Experimental 10x branch has passed offline mock unit tests but has no operator-deployed Windows 10x build or live certification.

The current 10x Futures canonical signal builder does not emit `protective_stop_policy_id` or `protective_stop_loss_price`; the engine requires both for entry. This is deliberately **FAIL-CLOSED**. Never synthesize an ARMED file to defeat it.

The 10x branch's mock test confirms that the MEXC order transport *would send* `stopLossPrice`, `lossTrend=2`; published MEXC docs list those fields. But no independently authorized real-exchange evidence of an accepted linked order, actual stop presence, trigger, partial fill behavior or remote survival is supplied. Stop APIs/stop placement can fail or execute at worse prices. Offline mocks are not proof of broker protection.

Position restart/triggered stop requires robust reconciliation of both trade ledger and live broker state; current branch returns reconciliation-required for missing position but does not prove realized close/exact economics after a stop trigger. A manual or host-offline gap must never be assumed flat or safe. Current 10x execution has no attributable closed 10x performance or prospective net-positive edge.

### Deterministic verification

Run offline at repo root, no credentials:
```sh
cd crypto_edge_radar
python -m unittest tests.test_options_v21_10x_final_truth_gate -v
python scripts/options_v21_10x_final_truth_gate.py
```
The tool reproduces frozen bridge values, inspects checked-in source and emits machine-readable `NO_GO_LIVE_10X`. For a hard error when no GO exists, use `--require-go` (exit 3). No account reads, network requests, credentials, trades or exchange mutation.

### Final operator action

**Do not start the installed executor. Keep the Windows scheduled task Disabled and ARMED absent. No additional user action on the PC is needed to establish this verdict.**

For a new legitimate GO candidate: freeze an economically distinct execution fork before looking at its forward outcomes, including verified venue/fee structure, broker-side stop placement/proof, maker/taker feasibility, cost/slippage/funding budgets, independent stop/recovery fault injection and statistically informative prospective net return. A hypothetical maker improvement is not the same thing as an executable edge; no post-outcome optimization.

**Closeout state: DECIDED / LIVE 10X NO-GO / RESEARCH CONTINUES ONLY ON DISTINCT PRE-REGISTERED FORKS.**
