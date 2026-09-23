# TVSQZ-001 — DISCOVERY CLOSEOUT / TOMBSTONE

Date: 2026-09-23  
LAB_ID: `TVSQZ-001`  
Parent mission: `TVSC-001`  
Family: TradingView Squeeze Momentum / volatility compression-release  
Governance: `CRYPTO-LAB-GOVERNANCE-V4.0-DEATH-FROZEN`

## Frozen question

Does the exact prospectively frozen LazyBear-style squeeze release state (BB20×2 inside KC20×1.5, true-range KC) predict abnormal realized volatility over the next four completed 1H bars relative to the trailing 20-bar causal volatility baseline?

## Canonical execution

Scope: Discovery 2022-01-01 through 2023-12-31 only.  
Venue/source: Binance USD-M Futures public monthly 1H archives.  
Universe: BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT.  
Source bundle SHA256: `ace6ee45c4c8b255576be5ac45f887c8a367c0e2e5327e3a23b3d241f159d367`.

Protected periods opened: **NONE**.  
Live execution: **false**.  
Merge to main: **false**.

## Stage A result

Total release events: **3,660**.  
All six symbols exceeded the frozen per-symbol sample gate.

Overall median future-RV ratio: **0.7925851603**.  
Frozen 2,000-replicate bootstrap 95% interval: **[0.7458177519, 0.8307258377]**.

Frozen pass requirement:
- overall median >= 1.20;
- lower bootstrap 95% > 1.05;
- at least 4 symbols with median > 1.0.

Observed per-symbol medians:
- BTCUSDT: 0.7938807604
- ETHUSDT: 0.7660970560
- SOLUSDT: 0.9087475048
- BNBUSDT: 0.8362608923
- XRPUSDT: 0.7252765044
- DOGEUSDT: 0.7171537623

Symbols with median > 1.0: **0 / 6**.

## Frozen classification

Scientific verdict: **NO_EDGE**  
Operational lifecycle: **CLOSED_EXACT**  
Mechanism state: **FALSIFIED_EXACT**

The exact tested claim did not merely miss the 1.20 threshold; the observed median was below 1.0 in every symbol. Under the frozen contract this exact experiment is terminal.

## Directional Stage B

**NOT OPENED.**

The protocol required Stage A to pass before the momentum-direction trade outcome could be evaluated. Because Stage A failed, directional PnL was intentionally not evaluated.

## Forbidden rescues

Do not:
- lower the 1.20 threshold after seeing this result;
- shorten/lengthen the four-hour horizon under TVSQZ-001;
- select SOL because it was the least-negative asset;
- change BB/KC parameters under the same LAB_ID;
- switch timeframe or venue to rescue the result;
- open 2024/2025/2026;
- inspect directional Stage B outcomes;
- relabel this exact result as unresolved.

## Successor boundary

A successor is permissible only under a **new LAB_ID** if it introduces material causal novelty under Governance V4. A different squeeze parameter, timeframe, holding period, asset subset, or directional overlay is not sufficient novelty.

This tombstone is the anti-duplication authority for future TradingView-census work.
