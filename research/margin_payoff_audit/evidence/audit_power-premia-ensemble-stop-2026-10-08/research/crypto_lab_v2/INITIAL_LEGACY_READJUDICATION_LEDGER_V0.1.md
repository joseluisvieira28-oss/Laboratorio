# CRYPTO LAB V2 — INITIAL LEGACY READJUDICATION LEDGER V0.1
Date: 2026-10-07
Scope: TRIAGE ONLY. NO RETROACTIVE SURVIVES.

This ledger uses existing outcomes only to classify what the old evidence can and cannot say.
It does not reopen protected data and creates no trading authority.

| Family | Legacy state observed | V2 readjudication | Priority | Reason / next legitimate action |
|---|---|---|---|---|
| LIQUIDATION-FLOW-FWD-001 | PARTIAL_SOURCE__ACTIVATION_BLOCKED; BTC source emitted valid events, ETH did not; no outcomes opened | SOURCE_BLOCKED/PARTIAL, not NO_EDGE | Medium source-only | Continue only under a new committed source-only boundary. Do not spend a scientific shot until source and power gates pass. Existing min-N rules are not automatically V2 power evidence. |
| CROSS-VENUE FUNDING/BASIS | PROVENANCE_RECOVERY_BLOCKED_NOT_NO_EDGE; replication inconclusive; diagnostics negative but non-canonical | SOURCE/PROVENANCE_BLOCKED + INCONCLUSIVE | Low until source unlock | Do not call dead. Reopen only if exact official provenance becomes available. No third-party substitute rescue. |
| BTC-OPTIONS-VRP-001 | Parent Discovery PASS; historical executable BBO source unavailable; execution unadjudicated; forward BBO collector health PASS | PHENOMENON_SUPPORTED / HISTORICAL_EXECUTION_SOURCE_BLOCKED / FORWARD_DATA_BUILD_CANDIDATE | HIGH | Strong fit to risk-transfer premium research. Do not infer profitability from discovery. Build/retain forward executable BBO evidence and require V2 mechanism/accessibility/power freeze before any future outcome analysis. |
| COINBASE-BINANCE-LEADLAG-001 | DATA_FAILURE / HYPOTHESIS_NOT_ADJUDICATED; free/public source recovery exhausted; non-canonical diagnostics negative | SOURCE_BLOCKED, not NO_EDGE | Low | Paid first-party data is a legitimate reopen trigger, but old diagnostics do not justify spending money. No new attack unless source economics change materially. |
| BTC-OPTIONS-EXPIRY-REVERSAL-001 | Discovery weak positive; independent 2024 OOS N=12 failed frozen support/stress gates; 2025/2026 remained locked in the cited closeout | LEGACY_INCONCLUSIVE / UNDERPOWERED_SUSPECT, not a clean NO_EDGE_AT_H under V2 | BANK / low-medium | Monthly event rate makes modest edges hard to confirm. Use old data only for power planning; do not reopen as a survivor. New untouched data may be accumulated prospectively under unchanged rules if the economically meaningful H justifies the wait. |
| FUNDING-CASH-CARRY-001 | N=131; positive funding component but 30 bps all-in cost overwhelmed 24h carry; bootstrap CI strongly negative net30 | EXECUTION_BLOCKED_FOR_TESTED_COST_MODEL; exact MVE terminal | Low on MEXC taker route | Legacy gross economics are only a few bps per 24h. The user's later MEXC audit observed about 15.9 bps taker round-trip, still above this family's inferred pre-cost mean. Same route is not attractive. Only a genuinely cheaper, pre-frozen execution path would justify a new family. |
| DEX-LIQUIDITY-PROVISION-001 | Source PASS and pre-discovery freeze; fixed sample floors and correlation/ratio gates; hypothesis predicts future RV, not direct PnL | V2_POWER_GATE_REQUIRED_BEFORE_OUTCOMES; MECHANISM-TO-PNL GAP | Medium research, low immediate monetization | If outcomes remain unopened, retrofit only BEFORE access: define economic service/risk/accessibility and derive power from H rather than fixed N=2000/1000. Descriptive volatility predictability is not yet an accessible trading edge. |
| LICP-HIST-XALT-003 | Historical holdout survivor, N=35, gross >16 bps transfer hurdle; explicitly not executable PnL | SURVIVOR_EVIDENCE_PRESERVED / EXECUTION_UNPROVEN | High forward only | Do not rewrite historical verdict. Next legitimate gate is the already-defined forward transfer/live-trigger dependency. V2 should enter at the next untouched stage, not retroactively change the holdout. |

## Quantitative planning note — BTC-OPTIONS-EXPIRY-REVERSAL-001
Using the already-open 2024 OOS returns only as a nuisance-variance planning input:
- sample sd ≈ 53.7 bps/trade;
- one-sided alpha 5%, target power 80%, iid analytical approximation;
- approximate N required to detect H:
  - H=5 bps → ~714 events
  - H=10 bps → ~179
  - H=15 bps → ~80
  - H=20 bps → ~45
  - H=30 bps → ~20

This is NOT a new verdict and does NOT authorize choosing H=30 because it needs fewer events.
H must come from economics before new outcomes.
The calculation simply shows why N=12 cannot settle modest monthly effects.

## Cost-accessibility note — carry
The user's separate MEXC fee audit later observed approximately 7.95–8 bps per taker fill, about 15.9–16 bps round-trip.
That later cost evidence does not rewrite the old FUNDING-CASH-CARRY-001 result.
It does show why V2 must model the actual operator route rather than an arbitrary universal cost assumption.

## Current priority order from this first pass
1. BTC-OPTIONS-VRP-001 — forward executable-data build + V2 power/accessibility design.
2. LICP-HIST-XALT-003 — preserve survivor; continue only at next untouched forward-transfer gate.
3. Source-only Liquidation Flow — finish source eligibility before any power/outcome work.
4. DEX-LP mechanism — retrofit V2 before outcomes if still outcome-blind.
5. BTC Options Expiry Reversal — bank; low event rate makes small-edge confirmation slow.
6. Funding Cash Carry tested route — low priority unless a materially cheaper execution path is independently available.
7. Coinbase-Binance lead-lag / Cross-venue provenance-blocked families — no further attack until source conditions genuinely change.
