# INDEX-CROSSVENUE-001 — authority reconciliation, 2026-10-05

## Decision
The handoff conflates distinct families. INDEX-CROSSVENUE-001 is a user task label: exact literal absent from all 768 fetched remote ref tips and from all-history pickaxe search. It is not an existing scientific family ID in this snapshot. No index forward authority inherits the equity overshoot freeze.

Retain the latest NAS100 canonical verdict:
`NO_NAS100_CROSSVENUE_OOS_SURVIVOR_AT_FROZEN_V07_GATE`.
SP500 cross-venue retains `NO_EDGE_AT_FROZEN_V04_GATE`.
No new outcomes, live books, parameters, or forward samples were opened in this audit. No collector was started. This is a documentary reconciliation, not a new scientific freeze or a new SOURCE_BLOCKED result.

## Audit scope and reproducibility
Full public Git clone (not shallow), all 768 remote ref tips and reachable history, no tags returned. Audited index branches, global-asset branches, overshoot source/binding/rule/closeout/shadow/workflows, NAS100 amendments and successor closeouts. No AGENTS.md found in selected trees or workspace ancestors checked.
Exact-ID tip search: batched git grep over refs/remotes/origin.
History search: git log --all -S INDEX-CROSSVENUE-001; no matches.
FOREX-MACRO-SHOCK-001 history search: no matches (does not rule out differently named prior authority).
GitHub workflow run metadata was independently read for runs 37195112899, 37192442631, 37283930479, 37284578918; all completed/success, with head SHA matching the named runner provenance. Economics below are canonical closeout values, not a fresh recomputation from ZIPs. Artifact hashes are inherited receipts; ZIP bytes were not downloaded/rehashed in this audit.

## Distinct authorities
| Family | Instruments / external reference | Authority / latest verdict |
|---|---|---|
| NAS100 level dislocation V0.7 | NAS100_USDT / Hyperliquid xyz:XYZ100, xyz DEX | e7180129 rule; 456046f2 pre-outcome freeze; ab4df0ed closeout; NO_NAS100_CROSSVENUE_OOS_SURVIVOR_AT_FROZEN_V07_GATE |
| NAS100 leadlag V0.6 | NAS100_USDT / Hyperliquid xyz:XYZ100 | 416171db rule; e644ea6b freeze; 2ed46738 closeout; UNDERPOWERED_NO_PROMOTION_AT_FROZEN_V06_GATE |
| SP500 leadlag V0.4 | SPX500_USDT / Hyperliquid xyz:SP500 | 1b87ef3d rule; fe00c336 freeze; 84539dd1 closeout; NO_EDGE_AT_FROZEN_V04_GATE |
| SP500 basis V0.2 | SPX500_USDT contract / MEXC index; not an independent external venue | 82ff31d1 rule; 9a56cefe freeze; 9e574bcd holdout; HOLDOUT_PASS_FORWARD_SHADOW_ELIGIBLE; standard API EXECUTION_FEE_BLOCKED_STANDARD_API |
| Equity/ETF overshoot V1.0, shadow V0.2 | 35 individual stock/ETF perpetual mappings, MEXC / Binance + Bitget | 634588c3 rule; 2bbbf080 binding; 8f7a09f5 freeze; 214c8a4b closeout; 475e739e shadow freeze; cbaaa3b3 workflow HEAD |

NAS100 source V0.5 identity blocker was superseded by amendment 09050cc4 and targeted proof f6fc4f1d: xyz:XYZ100 was omitted from the semantic alias scanner. Resolved source verdict: HYPERLIQUID_NAS100_SOURCE_PASS__XYZ_XYZ100. NAS100 dislocation V0.6 then failed historical coverage before scoring (09ba835f); V0.7 moved the window under a pre-outcome boundary-only freeze and closed with zero events. Do not resurrect the obsolete identity blocker.
SP500 resolved source verdict: HYPERLIQUID_SP500_SOURCE_PASS__XYZ_SP500, binding 07f6845b. Public/free source bindings exist; failed science is not missing source.

## Definitive explanation of Binance/Bitget discrepancy
The survivor binding at 2bbbf080 lists:
MSTR, INTC, AAPL, GOOGL, AMD, COIN, META, HOOD, MSFT, AVGO, TSM, AMZN, ONDS, RKLB, BABA, IREN, MRVL, PLTR, NFLX, ARM, CRWD, PDD, CRWV, QCOM, LLY, CSCO, JPM, WMT, IBM, CAT, COST, SMCI, VRT, ASML, QQQ.
Each has a frozen MEXC target and Binance/Bitget equivalent. NAS100_USDT and SPX500_USDT are absent. QQQ is an ETF leg; its presence does not turn this universe into NAS100 or create a synthetic NAS100/SP500 reference basket.
External consensus is the mean of each instrument's Binance and Bitget 5-minute returns. Simultaneous qualifying instruments form an equal-weight event basket, then daily means form the scientific reporting unit. This aggregation is not an index replication architecture.

The reported 143 event baskets / 17 dates / +20.0820 mean daily gross / +4.0820 after 16 bps belong only to this equity/ETF family. Never transfer them into INDEX.

## Canonical measurements and gates
NAS100 V0.7: all 16 cells N=0; admitted events=0; triggered sessions=0; gross/net means undefined, not zero. Source overlap 4,860/4,860 minutes over 2026-10-01 through 2026-10-04 08:59 UTC. No OOS selected/opened. Cost scenarios 0/2/5/10/12/14/16/20 bps; no executed fees. No notionals defined for this closed research family.
NAS100 leadlag V0.6: no cell N>=20; widest cells N=15/14/13/11 at 1/2/5/15 minutes; no promotion.
SP500 cross-venue V0.4: widest cell 4 events; zero eligible/Holm-selected cells; gross +1.417/+3.942/+2.915/+2.392 bps for 1/2/5/15 minutes, insufficient for the gate.
SP500 basis V0.2: 654 accepted signals, mean gross +0.5177567737 bps; separate internal-index convergence family. Standard taker fee assumption 16 bps would imply fee-only -15.4822432263 bps, before spread/slippage. No index forward evidence claimed.

Equity shadow V0.2 freeze verified: 13:30–20:00 UTC; closed-candle scan 13:35–19:55; 5m lookback; leader dispersion <=10 bps; abs MEXC move >=40 bps; abs excess >=35 bps; same-sign rule; fade excess; +5m exit; global cooldown 10m; simultaneous equal-weight basket; daily reporting unit; notionals 10/25/50/100 USDT; taker book fills; primary 16 bps and sensitivity 12/14/20; >=30 admitted events and >=5 session dates. Canonical insufficient-sample label is EXECUTION_SHADOW_UNDERPOWERED, not an invented PASS.
No prospective shadow workflow runs were returned by the public branch-filtered Actions query at audit time (total_count=0). This establishes no retrievable run in that query, not a universal proof of zero observations. No current shadow economics or per-notional results are available.

## Operational audit (equity code, documented only)
At cbaaa3b3 the shadow workflow is push/path-triggered, with no schedule or workflow_dispatch. The prior trigger-environment bug is already fixed in cbaaa3b3; do not claim it newly repaired.
Static defects:
- LATE_SCAN logs but continues scoring historical minutes and then capturing current books: violates prospective fail-closed capture.
- pending events/results exist only in memory; receipt writes only at completion, losing state on interruption.
- no persistent timestamp deduplication or global segment/cooldown state; aggregator promised in receipt but not in shadow workflow.
- scans all 35 instruments serially before entries, and exits only after scan; no enforcement of entry/exit timing validity.
- contractSize defaults to 1 on missing/invalid metadata; invalid executable quantities must fail closed.
- no durable raw source byte/hash chain; no net-return/gate aggregator in this workflow.
No changes made to equity code because current authorization is exclusively INDEX. No evidence recovered for a Codex active-task-limit failure; that handoff assertion remains unverified.
INDEX collector/scheduler: no active frozen forward identified; closed research workflows are historical one-shots. Arming the equity collector under INDEX would be a methodology substitution.

## Changes and blockers
Corrected: documentary misattribution of the equity survivor to indices.
Code bugs corrected this execution: none; none belong to an authorized active INDEX forward.
Remaining blockers: no surviving NAS100/SP500 cross-venue candidate and no canonical index future-forward continuation freeze. Source identity is resolved historically; current route health was not re-probed because it cannot reverse the existing scientific closeout.
Next legitimate INDEX gate: a separately committed, pre-outcome authority for any untouched future continuation, explicitly governing the genuine index mechanism. Do not lower gates or inherit the equity overshoot freeze.
No main merge, account reads, private exchange APIs, orders, wallets, paid sources, exchange mutation, or live trading.

## NEXT-HANDOFF — preparation only
FOREX-MACRO-SHOCK-001: no outcomes opened, no implementation started. Exact ID absent from reachable history, but inspect differently named macro/FX authority before any activation, including macro-expectation-violation-v0.1, macro-transmission-001-v01, macro-transmission-v0.1 and mexc-event-futures-macro-postrelease-v013-source-gate-2026-10-03. Require public/free defensible references and a pre-outcome freeze. This paragraph authorizes no new family work.
