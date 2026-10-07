# MEXC MULTI-STABLE BASIS — SOURCE CHARTER V0.1

Date: 2026-10-07
Family ID: MEXC-MULTI-STABLE-BASIS-001
Status: SOURCE-ONLY / OUTCOME-BLIND

## Objective

Determine whether MEXC provides sufficiently complete public/free market-data routes to support a later, separately frozen study of same-underlying perpetual contracts settled/margined in different stablecoins.

Primary candidate underlyings:
- BTC
- ETH

Candidate contract triplets:
- BTC_USDT / BTC_USDC / BTC_USD1
- ETH_USDT / ETH_USDC / ETH_USD1

## Duplication check

Before this charter:
- repository branch-name search found no branch named for multi-stable, USDC-M, USD1-M, BTC_USDC, or BTC_USD1 scientific basis work;
- repository commit search found no commit matching multi-stable, BTC_USDC, BTC_USD1, USDC-M, or USD1-M.

This does not prove no historical mention exists in every blob of every ref; any later discovered prior authority takes precedence and this family must be reconciled before outcomes.

## Source-only questions

For every candidate contract, test public/no-auth availability of:
- contract metadata;
- ticker;
- depth;
- trades;
- funding rate;
- index price;
- fair price;
- 1-minute K-line.

Record only route health, response schema, timestamps, contract metadata needed for later execution normalization, and source hashes.

Do NOT calculate:
- cross-contract basis;
- returns;
- lead/lag;
- convergence;
- PnL;
- winner/loser labels;
- profitable thresholds.

## Stablecoin normalization source gate

A future basis study MUST NOT assume:
USDT = USDC = USD1 = 1 USD.

Before any economic outcome is opened, prove a public/free normalization route for:
- USDC/USDT;
- USD1/USDT;
- optionally USD1/USDC as a consistency check.

Public MEXC Spot pairs may be used if source health is reproducible. External public references may later be added by a separate pre-outcome amendment.

This V0.1 source gate may verify pair existence, schema and timestamps, but MUST NOT score depeg/basis outcomes.

## Source PASS

SOURCE_PASS requires:
1. both BTC and ETH each have all three candidate perpetual contracts active;
2. all six contracts expose usable public metadata, ticker, depth, trades, funding, index/fair and 1m K-line routes;
3. timestamps are sufficiently explicit to permit minute-level alignment;
4. contractSize / volUnit / minVol / priceUnit are present and positive;
5. USDC/USDT and USD1/USDT normalization routes are public/free and timestampable;
6. no authentication, account read or trading is required.

If BTC passes but ETH does not, classify PARTIAL_SOURCE_PASS_BTC_ONLY.
If normalization is unavailable, classify SOURCE_BLOCKED_STABLECOIN_NORMALIZATION.
If required contract routes are missing, classify SOURCE_BLOCKED_CONTRACT_DATA.

## After SOURCE PASS

Do not open economic outcomes yet.

Next step must be a separate immutable PRE-OUTCOME FREEZE defining:
- normalized basis formula;
- stablecoin conversion hierarchy;
- signal hypothesis;
- development/OOS/future boundaries;
- costs, spreads, funding cashflows and execution assumptions;
- dependence handling;
- PASS/FAIL gates;
- no-tuning declaration.

## Governance

No main merge.
No login.
No private endpoints.
No account reads.
No orders.
No wallets.
No exchange mutation.
No spending.
No live trading.
No outcome-driven source substitution.
No post-outcome tuning.
