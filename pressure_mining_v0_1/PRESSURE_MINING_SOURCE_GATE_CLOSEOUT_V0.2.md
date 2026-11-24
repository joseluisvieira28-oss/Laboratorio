# CRYPTO LAB — PRESSURE MINING SOURCE GATE CLOSEOUT V0.2

Date: 2026-09-27  
Status: SOURCE / MECHANISM ADJUDICATION COMPLETE FOR CURRENT V0.2  
Branch: pressure-mining-program-v0.1  
No market-return or PnL outcomes were opened.

## Canonical source-only execution

GitHub Actions run: 36333172871  
Job: 108658899784  
Artifact: 10936007015  
Artifact digest: sha256:48ed6de1b04a91ef479d43f184b2469ae82f96f824c2ad0eaab10403edfc7ad6

Source-probe receipt pre-self SHA256:
1683066fc8b58d006774595a5e6560fec45c6f48b314af23fb8c17973d582d5b

Hardened census receipt pre-self SHA256:
550b6c2174e92fcc7ac2551484500e065bb9fcc5370c81f6e21d192aed7fcb4b

## 1. COMPOUND-INVENTORY-LIQUIDATION-001

Current state: SOURCE_CENSUS_PARTIAL / ARCHIVE SANITY NOT PROVEN.

The earlier V0.1 zero-log SOURCE_CENSUS_PASS is explicitly retracted.

Why:
- official Compound source and deployment identity are valid;
- the economic primitive remains materially distinct: protocol-owned seized collateral inventory and later disposal;
- however public RPC archive routes could not prove the known historical AbsorbCollateral anchor receipt and corresponding eth_getLogs recovery;
- therefore a zero-event census cannot be treated as evidence of a zero-event population.

Routing:
- mechanism remains scientifically open;
- no Discovery;
- no market-return layer;
- reopen source census only when a legitimate archive/indexed route recovers the historical anchor and both AbsorbCollateral / BuyCollateral event populations.

This is not NO_EDGE.

## 2. PENDLE-PT-MATURITY-CONVERGENCE-001

Source state: SOURCE_CENSUS_PASS.  
Mechanism routing: MECHANISM_DESCRIPTIVE / DISCOVERY_NOT_JUSTIFIED_AS_DEFINED.

Source evidence:
- 802 markets enumerated;
- 493 Ethereum markets;
- 107 Ethereum markets expired before 2025;
- 10/10 sampled historical coverage probes returned timestamped data;
- historical schema exposes baseApy, impliedApy, maxApy, timestamp, tvl, underlyingApy;
- market metadata exposes accountingAsset, expiry, PT/YT identities, protocol and points/reward metadata.

Mechanism adjudication:
PT maturity convergence is contract mechanics: PT is a principal claim redeemable at maturity for the accounting asset. Raw convergence-to-redemption is therefore not a sufficient alpha question.

No convergence statistic or PnL was computed.

## 3. PENDLE-FIXED-VARIABLE-YIELD-PREMIUM-001

State: DESIGN_ONLY / SOURCE_METADATA_FIRST / OUTCOMES LOCKED.

Metadata risk discovered before outcomes:
- 73 / 107 expired Ethereum markets carry non-empty points metadata;
- 107 / 107 carry non-empty reward-token metadata;
- the population spans many distinct protocols and accounting assets.

Consequence:
A naive fixed-vs-variable comparison can silently omit economically material incentives. No outcome test is allowed until point-in-time treatment of points/rewards and the population rule are prospectively frozen.

This is a source/economic-definition blocker, not a negative result.

## 4. LIDO-WITHDRAWAL-QUEUE-PRESSURE-001

Current state: SOURCE_PASS_PROSPECTIVE_ONLY.

Primary source:
official Lido Withdrawals API
https://wq-api.lido.fi/v2/request-time/calculate

Observed source gate:
- HTTP 200;
- non-empty JSON;
- top-level schema contains nextCalculationAt, requestInfo, status;
- response payload hashed;
- canonical WithdrawalQueueERC721 contract bytecode independently present through public RPC.

Historical archive is NOT claimed as passed and is not needed for the new-ID source gate.

Contamination firewall:
- 2023-2024 market-response outcomes from the prior stETH redemption lineage remain unusable as pristine evidence for this new queue-pressure hypothesis;
- the new ID inherits zero promotion credit;
- new queue observations may be collected prospectively;
- no price direction, threshold, horizon or economic translation has been frozen.

## 5. Rejected / duplicate-dense routes

MORPHO basic HF/liquidation port:
source feasible, but no lab opened because a basic port is not materially novel versus existing borrower-state / liquidation-convexity research.

Generic Hyperliquid funding/carry:
not opened; generic funding/carry surface is duplicate-dense without a materially new pressure primitive.

## Final routing

COMPOUND-INVENTORY-LIQUIDATION-001 -> SOURCE_FIRST / BLOCKED ON HISTORICAL ARCHIVE SANITY

PENDLE-PT-MATURITY-CONVERGENCE-001 -> MECHANISM_DESCRIPTIVE / DO NOT OPEN RAW-CONVERGENCE DISCOVERY

PENDLE-FIXED-VARIABLE-YIELD-PREMIUM-001 -> SOURCE_METADATA_FIRST / ECONOMIC COMPLETENESS REQUIRED

LIDO-WITHDRAWAL-QUEUE-PRESSURE-001 -> SOURCE_PASS_PROSPECTIVE_ONLY / ELIGIBLE FOR SOURCE-ONLY FORWARD COLLECTION

## Firewalls

market_outcomes_opened=false  
price_returns_computed=false  
pnl_computed=false  
protected_holdout_opened=false  
post_outcome_tuning=false  
live_trading=false  
orders=false  
exchange_mutation=false  
paid_data=false  
main_merge=false
