# USD-NET-LIQUIDITY-001 — OFFICIAL DISCOVERY CLOSEOUT

LAB: `USD-NET-LIQUIDITY-001`  
MVE: `UNL-FED-TGA-RRP-W1-001`  
Discovery run: `35058226109`  
Discovery artifact: `10431736516`  
Final classification: **DISCOVERY_FAIL_NO_PROMOTION**  
Economic companion: **POSITIVE_EXPECTANCY_UNCONFIRMED**  
Promotion: **FALSE**

## Frozen result

- N: `358` weekly trades (`186` long / `172` short)
- mean gross: `+33.5816644 bps/trade`
- mean NET10: `+23.5816644 bps/trade`
- mean NET20: `+13.5816644 bps/trade`
- median gross: `+68.9717790 bps`
- NET10 profit factor: `1.0721872`
- NET10 win rate: `51.67598%`
- moving 4-week block bootstrap, 5,000 reps, seed 230911: 95% CI for mean NET10 `[-73.5808337, +120.4094397] bps`

## Calendar stability — NET10 mean bps/trade

- 2018: `+189.1832` (N=50)
- 2019: `+56.4061` (N=51)
- 2020: `+142.1780` (N=50)
- 2021: `-163.0420` (N=53)
- 2022: `+22.2946` (N=52)
- 2023: `-126.3486` (N=52)
- 2024: `+60.9900` (N=50)

Non-negative 2018–2024: `5/7` — PASS.  
Non-negative 2021–2024: `2/4` — FAIL versus frozen minimum `3/4`.

## Frozen gate decision

PASS: N>=300; mean NET10>0; PF>1; 5/7 full-year stability; source/provenance firewalls.  
FAIL: bootstrap 95% lower bound >0; 2021–2024 stability >=3/4.

All gates were mandatory. The exact MVE therefore fails promotion despite positive pooled expectancy.

## Immutable evidence

- macro aligned SHA-256: `7706003c6cd99f0b4a44140a0db8e03967722b44e3e4be58a745d5af23751219`
- weekly deltas SHA-256: `b13bdabe229da799f49ef0563fe7085b9cf70ea85d1ecbed5318bc8ef2ce8728`
- BTC market manifest SHA-256: `3540afc9a69b32c128a60bca5ec6734dfd6e7a2b0eb805a7cb72215318bb2549`
- trades SHA-256: `1979154465993699ad2829ce2eea45be0aa6a1338a4e5f7a1929b22417947b5f`
- result SHA-256: `b11efc358b1df9b61f9681d6364f23a5647b39742c7baa439137cbefc433f888`
- Discovery artifact ZIP SHA-256: `bb6cc61be53b5e6df6bffcddff6c7214ac776178868f170936e2327cf7bbda12`
- Drive evidence ID: `1vX6uNNwqGuEXvjsS7bvrHv2yQaeCXpU0`

## Scientific decision

The pooled sign strategy is economically positive after frozen costs, but inference and recent-period stability do not meet the prospectively frozen promotion standard. This exact one-week sign MVE is CLOSED. No inversion, thresholding, smoothing, z-score, alternative liquidity formula, different hold/cost, subperiod selection, long-only conversion or 2025 rescue is authorized under this MVE ID.

A materially different liquidity mechanism requires a new hypothesis ID and new prospective authority.

## Governance

2025 accessed: NO. 2026 accessed: NO. Live trading: NO. Exchange mutation: NO. Merge to main: NO. Post-outcome tuning: NO.
