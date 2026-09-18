# AAVE-RISK-PARAMETER-SHOCK-001 — PRIMARY MECHANISM CENSUS FREEZE V0.1

Date: 2026-09-18
Status: FROZEN BEFORE PRIMARY-MECHANISM VALUE DECODING / OUTCOME-BLIND

## Purpose

Conditionally after SOURCE_CENSUS_PASS, decode only the protocol configuration values required to enumerate the already-frozen primary mechanism: decreases in Aave V3 Ethereum collateral liquidationThreshold.

This is not Discovery and opens no borrower, liquidation-outcome or market outcome.

## Exact source and envelope

- Ethereum mainnet.
- Canonical PoolConfigurator: 0x64b761d848206f447Fe2dd461b0c635Ec39EbB27.
- Frozen blocks: 16,490,000 through 21,525,890 inclusive.
- Hard timestamp ceiling: 2024-12-31T23:59:59Z.
- Event: CollateralConfigurationChanged(address,uint256,uint256,uint256).

## Exact decoding

For every canonical matching log, decode the three ABI data words as:
1. ltv
2. liquidationThreshold
3. liquidationBonus

The indexed asset address is the event's indexed asset topic.

For each asset, sort canonical events by (blockNumber, logIndex). The first observed event for that asset establishes the in-envelope baseline and is not itself classified as a decrease because no immediately prior in-envelope threshold is known.

A primary-mechanism event exists if and only if:
new_liquidationThreshold < immediately_previous_in_envelope_liquidationThreshold

No magnitude threshold is allowed.
No increase is a candidate.
No BorrowCap/SupplyCap/ReserveFrozen/ReservePaused/eMode event may substitute for this primary mechanism.

## Independence / clustering

All threshold decreases sharing the same transactionHash are one governance-execution shock cluster for sample-size purposes.
Raw per-asset decrease logs remain preserved, but later inference may not pretend same-transaction changes are independent observations.

## Frozen minimum source/sample gate

MECHANISM_CENSUS_PASS requires all of:
- at least 12 distinct threshold-decrease transaction clusters;
- at least 4 unique affected collateral assets;
- qualifying decrease clusters present in at least 2 UTC calendar years;
- zero duplicate canonical log identities;
- exact source envelope and protected-period firewall intact.

If any minimum fails:
INSUFFICIENT_PRIMARY_MECHANISM_SAMPLE

This is a source/sample verdict, not NO_EDGE.

## Allowed outputs

- counts of all CollateralConfigurationChanged logs;
- per-asset ordered threshold configuration history;
- threshold-decrease candidate rows;
- distinct transaction-cluster count;
- unique affected asset count;
- calendar-year coverage;
- structural checksums and transport diagnostics.

## Forbidden

- borrower balances or health factor;
- liquidation distance or liquidation-overhang predictor;
- future LiquidationCall outcomes;
- market prices or returns;
- PnL, win rate, PF or drawdown;
- 2025/2026 outcomes;
- live trading, orders, wallets or exchange mutation;
- main merge;
- switching the primary mechanism after seeing this census.

## Next gate after MECHANISM_CENSUS_PASS

A separate FINAL_PRE_DISCOVERY_PROTOCOL must prospectively freeze the causal on-chain target, event clock, horizon, event/non-event treatment, inference and any later market-impact MVE before any outcome is opened.
