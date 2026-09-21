# DEFI-LIQUIDATION-SHOCK-001 — PUBLIC RPC HISTORY PAGINATION FEASIBILITY CLOSEOUT V0.1

Date: 2026-09-21  
Status: **SOURCE FEASIBILITY COMPLETE / PROGRAM-ADDRESS PAGINATION NOT ADOPTED**

## Execution

GitHub Actions run: `35649242387`  
Job: `106497230850`  
Head commit: `eca1c99d693077d89285078966eb0f9da13d6fe1`  
Official public endpoint: `https://api.mainnet-beta.solana.com`  
Method: `getSignaturesForAddress`  
Page size: 1,000  
Boundary adjudication: false

## Result

All four one-page probes returned 1,000 historical rows with zero null block times and no transport failure.

Observed chronological coverage per 1,000 program-address signatures:

- Kamino Lend: **2,278 s = 0.6328 h**
  - linear pages/year estimate: ~13,853
- marginfi v2: **1,135 s = 0.3153 h**
  - linear pages/year estimate: ~27,804
- Drift v2: **101 s = 0.0281 h**
  - linear pages/year estimate: ~312,451
- Save/Solend: **17,046 s = 4.735 h**
  - linear pages/year estimate: ~1,851

## Adjudication

Classification:
`PUBLIC_RPC_PROGRAM_ADDRESS_PAGINATION_TECHNICALLY_AVAILABLE_BUT_NOT_DEFENSIBLE_FOR_CHRONOLOGICAL_CENSUS`

The official public RPC proves historical availability but program-address signature pagination is too high-volume for the frozen multi-year first-success/census task, particularly Drift and marginfi.

This route is therefore **not adopted** as a replacement for the frozen server-side indexed candidate census.

No BigQuery authority is superseded by this probe.

## Next source requirement

Seek a free/public historically indexed source capable of server-side filtering by:
- UTC time/slot range;
- exact program ID;
- exact instruction discriminator/tag/data prefix;
- transaction success/failure;
- immutable transaction signature/slot for subsequent official-RPC RAW verification.

Any replacement source requires a separate prospective source-authority amendment before boundary adjudication.

## Evidence

GitHub artifact:
- ID: `10660844252`
- SHA256: `8a6097ec2d9c378da421f8c3a6feb393d3d22c65a0e99e439ae1bb2f759da014`
- uploaded bytes: 638,460

Drive:
- `DLS_PUBLIC_RPC_HISTORY_FEASIBILITY_EVIDENCE_V0.1.zip`
- ID: `1a0Sg81cdgAQonuhhQ4Q21T_16yUnuPmg`

## Firewall

No transaction bodies were queried by the feasibility probe; no liquidation decoding; no prices, returns, PnL, direction, live trading, orders, wallets, exchange mutation, paid source or main merge.
