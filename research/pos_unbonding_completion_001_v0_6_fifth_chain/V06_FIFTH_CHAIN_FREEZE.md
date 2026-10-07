# POS-UNBONDING-COMPLETION-SUPPLY-RELEASE-001 — V0.6 FIFTH-CHAIN EXPANSION FREEZE

Date: 2026-10-07
Parent V0.5 head: 8fe8fab8cf0745f0ced3588fd97b8a10e9b29fa5
Market outcomes opened: NO
Candidate unbonding event counts below inspected before freeze: NO

Purpose: continue fifth-chain source remediation without altering V0.4/V0.5 evidence.

Frozen candidate order:
1. Crypto.org Chain / CRO
2. Evmos / EVMOS
3. Juno / JUNO

Selection rationale is source/mechanism/market-capability only: production Cosmos-SDK staking lineage, live during 2023-2024, and pre-2026 native-token market-source capability. Event richness is unknown and may not alter order.

A candidate passes source qualification only with:
- version-pinned native x/staking or proven equivalent lifecycle;
- two independently operated public/free historical paths covering relevant 2023-2024 heights;
- identical canonical fixed-height block hash/time/app-hash reconciliation;
- raw block + block_results lifecycle capability;
- a viable complete census route.

Inherited unchanged:
- completion interval 2023-01-01..2024-12-31 UTC;
- actual complete_unbonding is T_completion;
- cancellations/slashes/holds reconciled;
- materiality >=10 bps historical bonded stake;
- >=40 MATERIAL chain-days TOTAL across >=5 chains;
- no market outcomes, prices, returns, PnL;
- no trading/orders/wallet/account/private exchange endpoints/spending;
- main unchanged.

Stop candidate search at first source-qualified chain. Only then may a separately frozen census route inspect that chain's completion events.
