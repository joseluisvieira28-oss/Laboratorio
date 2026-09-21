# DEFI-LIQUIDATION-SHOCK-001 — PUBLIC RPC HISTORY PAGINATION FEASIBILITY FREEZE V0.1

Date: 2026-09-21  
Status: **SOURCE-ONLY FEASIBILITY / NOT BOUNDARY ADJUDICATION**

## Purpose

Measure whether official public Solana RPC signature pagination is technically capable of supporting a future chronological first-success source route.

This probe does **not** replace the already-frozen BigQuery first-success authority and does **not** adjudicate any first-success boundary.

## Endpoint and method

Endpoint: `https://api.mainnet-beta.solana.com`  
Method: `getSignaturesForAddress`

Exactly one page of at most 1,000 signatures is requested **before one pre-existing 2024-12-15 reference signature per protocol**.

No transaction bodies, prices, market returns, PnL or direction are requested.

## Frozen anchors

- Kamino Lend / program `KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD`
  - before signature: `37bfneBLcVoWnqWEoP7Y4EnJREUeaHeEYgnQ9kjBGpsN3tMjP2AceURMpbgQDeR8hmxZ4L5JVSokepJ7WhsuTDnK`
- marginfi v2 / program `MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA`
  - before signature: `4Woi6qL1sdzaFgTQkrLLqkvnUm9dncraHTWmcnsvpQ8B4EbVwUcMXpDBJT5YEZiFLXwSRhoWvJAkpbnwg4rBSxgH`
- Drift v2 / program `dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH`
  - before signature: `4HxbJXnf4mu5WybzTm6pgu5JbsAbU4hhyM7UKbiZ92dehj7MD6T2qWj1HcWZc2q32y3fFv5wFTSxRNfzHBNsef1d`
- Save/Solend / program `So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo`
  - before signature: `3kefBPaiAPXNDJrnsp6idVtovy1hPgYekLQvKcFf3X4aypJhXpaxGR2CKRP931tDxff46YGAMqfzFgVf4EwyBRzm`

## Measurements

Per protocol:
- returned row count;
- newest and oldest returned slot;
- newest and oldest blockTime;
- chronological span represented by one page;
- null-time count;
- transport status.

No liquidation discriminator decoding occurs in this probe.

## Interpretation

The result may support or reject further research into a public-RPC discovery route. It grants **no boundary credit**, **no SOURCE_DATA_PASS**, and no economic inference.

Any future replacement or supplementation of the frozen BigQuery boundary-search source requires a separate prospective source-authority amendment before adjudication.

## Firewall

source_only=true; outcomes=false; prices=false; returns=false; pnl=false; direction=false; live_trading=false; orders=false; wallets=false; exchange_mutation=false; paid_source=false; merge_main=false.
