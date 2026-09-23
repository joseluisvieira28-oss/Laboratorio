# USOPEN-VOL-002 / USOV-POSTETF-2024-001 — CLOSEOUT

Date: 2026-09-23  
Branch: `us-open-volatility-postetf-2024-v0.1`  
GitHub Actions run: `35921872685`  
Scientific verdict: **POSTETF_2024_EXACT_REPLICATION_FAILS**  
Lifecycle: **M4 REPLICATION — EXACT SPEC FAILED / MECHANISM PARTIALLY PRESERVED**

## Frozen question

Did the exact pre-ETF 09:30 ET crypto realized-variance concentration replicate after U.S. spot Bitcoin ETP trading began on 2024-01-11, using the same universe, 30-minute windows, variance estimator and threshold logic?

## Result

Post-ETF 2024 sample:
- 245 eligible U.S. trading dates;
- 1,470 symbol-days;
- pooled median OPEN/PRE = **1.990785x**;
- OPEN/PRE date-cluster bootstrap 95% = **[1.773612, 2.269498]**;
- pooled median OPEN/POST = **1.022627x**;
- OPEN/POST date-cluster bootstrap 95% = **[0.925591, 1.134768]**;
- 6/6 symbols have median OPEN/PRE > 1.10.

The exact frozen replication gate fails because the confirmatory OPEN/POST requirements do not pass:
- required pooled OPEN/POST >= 1.10; observed 1.022627;
- required bootstrap lower95 > 1.00; observed 0.925591.

The primary OPEN/PRE concentration does replicate strongly and broadly:
- BTC 2.739776x
- ETH 2.302931x
- SOL 1.897297x
- XRP 1.807540x
- DOGE 1.791842x
- BNB 1.717960x

## Structural comparison versus 2022–2023

Frozen pre-ETF baseline recomputation matches the parent source bundle exactly.

Baseline pooled OPEN/PRE = 1.964663x.  
2024 post-ETF pooled OPEN/PRE = 1.990785x.  
Point factor = 1.013296x.  
Independent date-cluster bootstrap 95% factor = **[0.877911, 1.196365]**.

Classification: **NO_DETECTABLE_SHIFT**.

Therefore there is no defensible evidence in this frozen comparison that the OPEN/PRE effect was amplified or attenuated after ETF launch. This is not an ETF-causality result.

## Interpretation boundary

The exact first-30-minute concentration specification does **not** replicate because OPEN is not sufficiently larger than the immediately following 10:00–10:30 window.

This does **not** justify declaring the 09:30 ET market-clock mechanism dead. Relative to PRE, the opening window remains approximately 2x in realized variance across all six symbols. The failed OPEN/POST gate indicates that elevated variance may extend beyond the first 30 minutes in 2024.

That persistence hypothesis was not frozen in this MVE and must not be tested here.

## Anti-rescue / firewall

Do not:
- drop the OPEN/POST gate retroactively;
- redefine success using OPEN/PRE only;
- change 30-minute windows;
- extend OPEN to 60 minutes under this MVE;
- select BTC/ETH only;
- exclude macro days after outcome access;
- open 2025 or 2026;
- compute directional PnL;
- merge to main;
- trade live.

A duration/persistence successor requires a new LAB_ID, new prospective freeze, and zero inherited promotion credit.

## Provenance

- parent/baseline source bundle SHA256: `a2b15380cc5cf6e71750db8a9af07abd2086df5dbd183cf96406d51b2746cc70`
- post-ETF 2024 source bundle SHA256: `87c448a6c5d2004cdf4ebd49985365821cb864222247c21b5c4cb78a45c38e86`
- 2025 and 2026 remain sealed.
