# DLS — INSTRUCTION TOKEN BALANCE RELATION DIAGNOSTIC FREEZE V0.2

Date: 2026-09-26
Status: SOURCE-ONLY / TRANSPORT DIAGNOSTIC / OUTCOME-BLIND

V0.1 recovered all three exact liquidation instructions with HTTP 200 but observed zero
transaction token-balance rows. That result is transport/query-shape fail-closed, not a source-data failure.

V0.2 changes no scientific population or decoder rule.

For the same Save0c, Save11 and Kamino exact reference slots:
- add exact discriminator filter (d8 for Anchor; d1 for native tags);
- add isCommitted=true to the instruction selector;
- retain transaction=true and transactionTokenBalances=true;
- request only token-balance identity/unit fields:
  account, preMint, postMint, preDecimals, postDecimals;
- record total returned tokenBalances before any transactionIndex filtering;
- record response block top-level keys and tokenBalance transactionIndex values;
- compare target mint+decimals only after transport shape is observed.

PASS remains exact 3/3 reference metadata equality.
If token balances remain absent, classify the raw relation route
INSTRUCTION_TOKEN_BALANCE_RELATION_RAW_PORTAL_NOT_MATERIALIZED and stop optimizing this route.

No amounts, prices, returns, PnL or outcomes.
