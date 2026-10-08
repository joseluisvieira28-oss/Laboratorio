# BTC-CONVEX-TREND-CAPTURE-001 — EXPANSION REPLICATION CLOSEOUT V0.1

**Date:** 2026-09-24  
**Experiment:** second independent cross-sectional replication  
**Universe:** XRPUSDT, DOGEUSDT, ADAUSDT, LINKUSDT, AVAXUSDT  
**Window:** 2021-01-01 through 2025-12-31  
**Timeframe:** 1h  
**Parent:** recovered V5 causal rule, unchanged  
**2026:** remained locked

## Authoritative source gate

Workflow run: **35920189830**  
Artifact: **10777925156**  
Artifact SHA-256: **8132e68db1e17be948387700cf27529b21effeab86d0ba835d2f0b05c8e17345**

Result: **PASS**

All five assets were source-valid:
- 43,824 / 43,824 economic hours each
- funding coverage complete
- official mark-price hierarchy satisfied
- maximum funding timestamp normalization deviation = 47 ms
- no interpolation, spot fallback or nearest-neighbor substitution

## Authoritative economic run

Workflow run: **35921780080**  
Artifact: **10778258822**  
Artifact SHA-256: **d35e75f61d518326b614b4106a56150ee02bc8465f7f582aae6269ff86ef8af1**

Frozen execution:
- commission 10 bps per side
- BASE adverse slippage 2 bps per side
- STRESS adverse slippage 5 bps per side
- official historical USD-M perpetual funding
- causal bar execution
- no retuning
- Parent only for adjudication

## Parent BASE results

| Asset | Trades | Net return | CAGR | PF | Max MTM DD | Funding | Net after removing top winner |
|---|---:|---:|---:|---:|---:|---:|---:|
| XRPUSDT | 136 | **-77.62%** | -25.87% | 0.636 | -88.18% | -1,354.60 | -11,293.33 USDT |
| DOGEUSDT | 166 | **-68.90%** | -20.83% | 0.799 | -75.58% | -1,626.13 | -12,073.50 USDT |
| ADAUSDT | 159 | **-72.53%** | -22.77% | 0.745 | -85.14% | -1,697.23 | -10,086.58 USDT |
| LINKUSDT | 161 | **-81.12%** | -28.36% | 0.665 | -83.31% | -1,689.89 | -10,187.20 USDT |
| AVAXUSDT | 173 | **-78.32%** | -26.35% | 0.777 | -85.96% | -1,454.16 | -11,323.25 USDT |

Family BASE:
- positive assets: **0 / 5**
- PF > 1: **0 / 5**
- positive after removing top winner: **0 / 5**
- equal-weight mean return: **-75.70%**
- median return: **-77.62%**

## STRESS

Family STRESS:
- equal-weight mean return: **-77.78%**
- positive assets: **0 / 5**
- PF > 1: **0 / 5**
- positive after removing top winner: **0 / 5**

## REPRO view

Even before BASE/STRESS slippage:
- equal-weight mean return: **-73.80%**
- positive assets: **0 / 5**
- PF > 1: **0 / 5**

Therefore the failure is not attributable to the frozen slippage overlay.

Funding is economically relevant, but the magnitude and REPRO failure show that funding alone does not explain the result.

## Frozen gate adjudication

Pre-registered expansion requirements:
1. >=3/5 positive BASE assets — **FAIL (0/5)**
2. >=3/5 BASE PF > 1 — **FAIL (0/5)**
3. STRESS family mean > 0 — **FAIL (-77.78%)**
4. >=2/5 positive after removing top winner — **FAIL (0/5)**
5. >=4/5 source-valid — **PASS (5/5)**
6. no provenance/causal blocker — **PASS**

Final adjudication:

# **CROSS_SECTION_EXPANSION_FAIL**

## Scientific consequence

The recovered Parent V5 cannot be described as a universal cross-crypto 1h edge.

Current evidence is heterogeneous:
- BTC causal retrospective diagnostic: survives
- first untouched basket ETH/SOL/BNB: survives
- second untouched basket XRP/DOGE/ADA/LINK/AVAX: fails decisively

The correct classification is therefore:

**SCOPE-LIMITED / HETEROGENEOUS MECHANISM — BOUNDARY UNKNOWN**

It is prohibited to:
- drop the failing assets and call the remaining subset universal;
- retune thresholds on the failed assets;
- switch timeframe to rescue them;
- reduce fees/funding assumptions to rescue them;
- open 2026 as a rescue sample.

## Allowed next work

Post-outcome mechanism diagnostics may compare surviving and failing assets to generate new hypotheses.

Such diagnostics:
- receive zero promotion credit;
- cannot retroactively validate the Parent;
- must freeze any new child hypothesis before opening untouched evidence.

Prospective shadow observation of the unchanged Parent is still allowed as research evidence, but no live capital authority is created by this closeout.

## State

**PARENT UNIVERSALITY: REJECTED**  
**FIRST UNTOUCHED BASKET: SURVIVES**  
**SECOND UNTOUCHED BASKET: FAILS**  
**GLOBAL EDGE CLAIM: NOT SUPPORTED**  
**LIVE TRADING: NOT AUTHORIZED BY THIS LAB**  
**MAIN MERGE: NOT AUTHORIZED**
