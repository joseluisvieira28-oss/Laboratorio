# AAVE-LIQUIDATION-OVERHANG-001 — TERMINAL REPLICATION CLOSEOUT V0.1

Date: **2026-09-19**
Status: **REPLICATION_NO_SIGNAL — CLOSED / NO RESCUE**

## Canonical Discovery 2023

Run: `35436923688`
Artifact: `10582547257`
Artifact digest: `sha256:9c80c3b64f540eee2a2e1f02b3b64867b584872195456afcc3a6214972fe5860`
Classification: `DISCOVERY_MECHANISM_PASS`

Frozen 2023 result:
- snapshots: **334**
- overhang-positive days: **334**
- positive liquidation-outcome days: **145**
- Spearman rho: **+0.2580235336860782**
- stationary bootstrap one-sided 95% lower bound: **+0.1394215970156347**
- largest realized-outcome day removed: **2023-08-17**
- rho after removal: **+0.2640034879723874**

All frozen Discovery gates passed.

Interpretation:
the exact 2023 Discovery supported the protocol-mechanism statement that higher latent liquidation overhang was associated with higher next-24h realized Aave liquidation debt notional.

This was mechanism evidence only. It was never market-edge or trading-strategy proof.

## Canonical Replication 2024

Run: `35438333758`
Artifact: `10584403183`
Artifact digest: `sha256:dbc62898100467d5ebf4dc29fcb1cf52e173705677034bf1b7d92c9b3d6424dc`
Classification: `REPLICATION_NO_SIGNAL`

Frozen 2024 result:
- snapshots: **365**
- overhang-positive days: **365**
- positive liquidation-outcome days: **296**
- Spearman rho: **-0.0007552268232980498**
- stationary bootstrap one-sided 95% lower bound: **-0.11081182181387964**
- largest realized-outcome day removed: **2024-08-05**
- rho after removal: **-0.0034172165315934904**

Replication gates:
- sample size: PASS
- overhang-positive days: PASS
- positive outcome days: PASS
- provenance/leakage: PASS
- rho > 0: **FAIL**
- bootstrap lower bound > 0: **FAIL**
- rho after removing largest outcome day > 0: **FAIL**

## Scientific verdict

The 2023 relationship did **not** replicate independently in 2024.

Canonical terminal classification:

`REPLICATION_NO_SIGNAL`

The exact lab is therefore closed.

Do not promote to a market MVE, shadow strategy, Tier 3, Tier 2, “near diamond”, micro-live or live execution.

## Anti-rescue

Forbidden for this exact LAB_ID:
- changing the 10% shock;
- selecting 5% or 20% diagnostics as replacement primary;
- changing snapshot hour;
- changing next-24h horizon;
- filtering assets/users/dates/regimes after the outcome;
- dropping 2024;
- opening 2025/2026 to rescue;
- changing statistic or bootstrap;
- creating a market-return/PnL layer from this failed replication;
- sign inversion or subgroup rescue.

Any materially different idea requires a new LAB_ID and a new prospective freeze before outcomes.

## Safety

No live trading, wallets, orders, exchange mutation, authenticated trading API, leverage, main merge or capital deployment was authorized or performed.

2025 and 2026 scientific data remain unopened for this lab.
