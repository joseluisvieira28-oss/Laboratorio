# BTC-CONVEX-TREND-CAPTURE-001 — FIRST UNTOUCHED CROSS-ASSET CLOSEOUT V0.1

**Date:** 2026-09-23  
**Parent:** recovered Quant Trailing v5 (Payoff Invertido)  
**Child:** Sticky-Trail H1  
**Window:** 2021-01-01 through 2025-12-31  
**Timeframe:** 1h  
**Universe:** ETHUSDT, SOLUSDT, BNBUSDT  
**2026:** LOCKED / UNOPENED FOR THIS EXPERIMENT

## Authoritative provenance gate

Final source gate:
- workflow run: 35918769955
- artifact: 10775718286
- artifact SHA-256: e16e764d8b355730c46979e58b91ea2505893eba601f5df9d341c3a118815045
- gate: CROSS_ASSET_SOURCE_GATE_V0.1F
- result: **PASS**

Coverage:
- ETH: 43,824 / 43,824 economic market hours
- SOL: 43,824 / 43,824 after exact official daily completion of 120 monthly-archive missing hours
- BNB: 43,824 / 43,824
- funding coverage complete
- max funding timestamp normalization deviation: 47 ms
- all funding marks resolved using frozen official hierarchy
- no interpolation, spot fallback or ordinary market-price fallback

## Authoritative economic run

Final untouched cross-asset validation:
- workflow run: 35918769969
- artifact: 10775714534
- artifact SHA-256: 236b053ad50704149c5702803722c8022bee99d9dba0565e6b25138992571032
- result: **SURVIVES**

Frozen costs:
- commission: 10 bps per side
- BASE slippage: 2 bps adverse per side
- STRESS slippage: 5 bps adverse per side
- official historical USD-M perpetual funding

## Parent V5 — BASE

| Asset | Trades | Net return | CAGR | PF | Max MTM DD | Funding | Net after removing top winner |
|---|---:|---:|---:|---:|---:|---:|---:|
| ETHUSDT | 100 | +96.12% | 14.42% | 1.212 | -54.28% | -5,508.51 | +2,666.93 USDT |
| SOLUSDT | 163 | +91.23% | 13.84% | 1.141 | -58.97% | -2,653.55 | +1,845.65 USDT |
| BNBUSDT | 102 | +255.84% | 28.90% | 1.266 | -58.20% | -956.43 | +5,983.30 USDT |

Family:
- positive assets: **3 / 3**
- PF > 1: **3 / 3**
- positive after removing top winner: **3 / 3**
- equal-weight mean return: **+147.73%**
- median asset return: **+96.12%**

## Parent V5 — STRESS

5 bps adverse slippage per executed side plus commission and funding:

| Asset | Net return | PF | Max MTM DD | Net after removing top winner |
|---|---:|---:|---:|---:|
| ETHUSDT | +89.18% | 1.200 | -54.70% | +2,195.85 USDT |
| SOLUSDT | +92.52% | 1.135 | -59.38% | +655.55 USDT |
| BNBUSDT | +229.23% | 1.243 | -60.85% | +3,390.49 USDT |

Family:
- positive assets: **3 / 3**
- PF > 1: **3 / 3**
- positive after removing top winner: **3 / 3**
- equal-weight mean return: **+136.97%**

## Frozen parent gate adjudication

Pre-registered Parent requirements:
1. >=2/3 positive BASE assets — PASS (3/3)
2. >=2/3 BASE PF > 1 — PASS (3/3)
3. STRESS equal-weight family mean > 0 — PASS (+136.97%)
4. >=1/3 BASE asset positive after removing top winner — PASS (3/3)
5. no provenance/leakage blocker — PASS

Therefore:

**PARENT CROSS-ASSET REPLICATION = SURVIVES**

This gate explicitly does not authorize promotion or live trading by itself.

## Sticky H1 — descriptive comparison only

BASE:
- ETH: +60.77%, PF 1.132, DD -52.33%
- SOL: +107.47%, PF 1.147, DD -52.38%
- BNB: +202.16%, PF 1.205, DD -66.16%
- family equal-weight mean: +123.47%

Compared with Parent BASE:
- Sticky is better on SOL return and drawdown;
- Sticky is worse on ETH return;
- Sticky is worse on BNB return and drawdown;
- Parent has higher equal-weight family return.

Per the pre-freeze protocol, **no historical winner is selected** between Parent and Sticky.
Prospective evidence is required.

## Scientific interpretation

This is the first independent cross-asset evidence supporting the recovered mechanism.

The result is materially stronger than BTC-only retrospective evidence because:
- assets were frozen before outcomes were opened;
- parameters were not retuned by asset;
- causal execution was used;
- funding, commission and slippage were included;
- all three assets remained positive after removing their single largest winner.

Important remaining weakness:
- drawdowns remain very large, roughly 54%-59% for Parent BASE;
- PF remains modest, approximately 1.14-1.27;
- positive skew / trend-tail dependence remains part of the mechanism;
- this does not prove future profitability.

## State

**MECHANISM REPRODUCTION: PASS**  
**BTC CAUSAL DIAGNOSTIC: SURVIVES**  
**FIRST UNTOUCHED CROSS-ASSET REPLICATION: SURVIVES**  
**PROSPECTIVE FORWARD: NOT YET ADJUDICATED**  
**LIVE TRADING: NOT AUTHORIZED**  
**MAIN MERGE: NOT AUTHORIZED**
