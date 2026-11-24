# CRYPTO LAB — PRESSURE MINING PROGRAM V0.1

Date: 2026-09-27
Status: SOURCE / MECHANISM GATES ONLY
Repository: joseluisvieira28-oss/Laboratorio
Branch: pressure-mining-program-v0.1

## Mission

Shift new research away from generic pattern mining and toward directly observable economic pressure.

No protected market outcomes are authorized by this program.
No live trading, orders, wallets, exchange mutation, capital use, paid-data purchase, main merge or post-outcome tuning is authorized.

## Mandatory upstream gates

Every child must satisfy:
1. Negative Edge Map anti-duplication.
2. Diamond DNA mechanism-first preflight.
3. Governance V4 new-mechanism gate.
4. Point-in-time source feasibility before any outcome layer.

## Pressure scan result

### OPENED — COMPOUND-INVENTORY-LIQUIDATION-001
Primary family: CREDIT
Secondary: MICRO
Novel primitive: Compound III is structurally two-stage. An underwater account can be absorbed onto protocol reserves; seized collateral then exists as protocol inventory and may later be purchased at a discount through buyCollateral when reserve conditions permit.

This is materially distinct from Aave health-factor crowding or generic liquidation event counting because the measurable pressure is **protocol-owned collateral inventory awaiting disposal**, not merely borrower liquidatability.

Source-only first action:
- resolve official Comet deployment from compound-finance/comet roots.json;
- verify official AbsorbCollateral / BuyCollateral schema;
- verify public Ethereum RPC bytecode/log access;
- count/schema-check events only.
No asset returns, price response or PnL.

### OPENED — PENDLE-PT-MATURITY-CONVERGENCE-001
Primary family: RV
Secondary: CARRY
Novel primitive: Pendle PT is a tokenized principal claim redeemable at maturity for its accounting asset. The economic contract differs from generic perpetual/futures basis because the redemption anchor is explicit and maturity extinguishes the YT claim.

Source-only first action:
- public Pendle markets endpoint;
- historical market endpoint;
- immutable market/expiry/PT/accounting-asset identity;
- verify historical schema and timestamp coverage.
No convergence return, trade simulation or PnL.

### PREPARED PROSPECTIVE-ONLY — LIDO-WITHDRAWAL-QUEUE-PRESSURE-001
Primary family: FLOW
Secondary: SUPPLY / MR
Novel primitive: aggregate withdrawal-queue backlog and finalization throughput, not one-at-a-time hypothetical redemption execution.

Why not historical Discovery now:
- STETH-REDEMPTION-BASIS-002 already opened 2023-2024 family outcomes and completed with only 2 non-overlapping redemptions;
- reusing that outcome period for a newly conceived queue-pressure rule would create contamination.
Therefore this new ID earns zero inherited promotion credit and is prospective-only until fresh evidence is explicitly authorized.

Source-only action may verify queue contract/event availability without market-price outcomes.

### NOT OPENED — MORPHO BASIC HF/LIQUIDATION
Source quality is strong, but a simple health-factor / liquidation-distance port would be too close to existing Aave borrower-state and liquidation-convexity work. "New protocol" alone fails the V4 causal-novelty gate.

A future Morpho lab would require a mechanism unique to isolated Morpho markets, such as cross-market asynchronous LLTV/oracle liquidation geometry, and must prove novelty before opening an ID.

### NOT OPENED — HYPERLIQUID FUNDING
Official funding history is publicly queryable, but the mechanism falls inside a heavily mined generic carry/funding zone. Official deep historical archive routes also use requester-pays for S3. No new lab is justified without a materially new pressure primitive.

## Routing priority after source gate

1. Compound protocol-inventory liquidation — PRIORITY A.
2. Pendle PT maturity / executable redemption anchor — PRIORITY A.
3. Lido queue-pressure prospective source collection — PRIORITY B.
4. Morpho isolated-market novelty design — IDEA ONLY.
5. Generic funding/carry variants — REJECT / DUPLICATE-DENSE.

## Hard firewall

source_only=true
market_outcomes_opened=false
protected_holdout_opened=false
pnl_computed=false
strategy_parameters_tuned=false
live_trading=false
orders=false
exchange_mutation=false
wallet_actions=false
paid_data=false
main_merge=false
