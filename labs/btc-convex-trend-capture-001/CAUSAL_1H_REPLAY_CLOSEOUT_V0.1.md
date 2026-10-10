# BTC-CONVEX-TREND-CAPTURE-001 — CAUSAL 1H REPLAY CLOSEOUT V0.1

**Date:** 2026-09-23  
**Protocol:** CAUSAL_1H_REPLAY_PROTOCOL_V0.1  
**Workflow run:** 35911267608  
**Artifact:** 10772639953  
**Artifact SHA-256:** 5ecf95063510a699e6c00baa9c0e1d3d9d7e688dcd86f8fecad18e726963a9fd  
**Status:** CAUSAL EXECUTION DIAGNOSTIC SURVIVES / EDGE STILL UNPROVEN

## Frozen replay boundary

Start:
- 2020-03-01 00:00 UTC
- equity = 10,489.94 USDT

End:
- 2026-06-30 23:00 UTC

The replay preserved:
- exact recovered entry rule;
- 95% exposure;
- 0.10% commission each side;
- 4% initial stop;
- 12% trailing distance;
- non-latched +5% close-based trail selection.

It removed:
- same-bar historical reentry from final current-bar information;
- access to final current-bar high/close before bar completion.

No funding or slippage was added in this first apples-to-apples execution-integrity diagnostic.

## Causal replay result

- closed trades: **93**
- wins: **23**
- losses: **70**
- win rate: **24.73%**
- realized ending equity: **39,245.41 USDT**
- realized net PnL: **+28,755.47 USDT**
- realized return on frozen start equity: **+274.12%**
- approximate CAGR: **23.2%**
- profit factor: **1.311**
- max closed-equity drawdown: **-40.75%**
- no open position at replay end.

Tail dependence:
- net after removing largest causal winner: **+9,408.82 USDT**
- net after removing top three causal winners: **-20,111.79 USDT**

The mechanism therefore remains strongly right-tail dependent.

## Supplied TradingView comparator on same boundary

Retrospective supplied ledger:
- closed trades: **94**
- net PnL after boundary: **+37,452.81 USDT**
- ending equity from same starting equity: **47,942.75 USDT**
- return: **+357.04%**

## Execution-contamination impact

Difference:
- **8,697.34 USDT** less net PnL in the causal replay;
- approximately **23.2%** of the supplied TradingView net PnL on the same boundary;
- return difference: approximately **82.9 percentage points**.

Thus historical order-fill recalculation materially inflated the supplied result.

However:

**removing the identified same-bar foreknowledge and current-bar final-value access did NOT destroy the mechanism.**

The causal replay still shows substantial positive retrospective economics under the same fee assumptions.

## Scientific interpretation

This is a meaningful survival result for mechanism integrity, but it is NOT proof of edge because:
- BTC 2020-2026 outcomes were already observed before this replay;
- the replay implementation was created after source inspection;
- funding is not included;
- slippage is not included;
- the signal and timeframe were already known to perform historically.

The correct interpretation is:

**LOOKAHEAD CONTRIBUTED MATERIALLY, BUT DOES NOT EXPLAIN THE ENTIRE 1H RESULT.**

## Next valid work

1. freeze an economic cost layer for perpetual execution:
   - funding;
   - realistic slippage;
   - venue fees;
   - gap handling;

2. validate the exact original rule with no retuning on untouched evidence;

3. keep the sticky-trail child hypothesis separate from the parent;

4. only independent cross-asset/prospective evidence can create promotion credit.

## Verdict

**CAUSAL EXECUTION DIAGNOSTIC: SURVIVES**  
**RETROSPECTIVE MECHANISM: INTERESTING**  
**INDEPENDENT EDGE: UNPROVEN**  
**PROMOTION: NOT OPEN**

No live trading, exchange mutation or main merge is authorized.
