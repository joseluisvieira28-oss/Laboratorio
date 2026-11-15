# LCOD MULTI-BORROWER SAME-BLOCK SCALE GATE V0.1

Frozen: 2026-09-25
Stage: SOURCE / SNAPSHOT CONSISTENCY
Outcomes: CLOSED

## Parent evidence

- FULL_CENSUS_FRESH_PRICE_RECON_PASS:
  2,354 / 2,385 debt-bearing indexed borrowers eligible = 98.7002%.
- BLOCK_PIN_FIXTURE_PASS:
  one debt-bearing borrower reconstructed at one finalized Ethereum block with
  exact HF parity (relative error 0).

## Deterministic cohort

At probe start:
1. choose one Ethereum finalized block N;
2. enumerate current Ethereum v4 borrow-holder candidates through official Aave
   MCP only for candidate discovery;
3. decode each opaque reserve ID to its official spoke + numeric reserve;
4. deduplicate candidate (spoke, wallet) pairs;
5. sort by:
   spoke address, then SHA256(lowercase wallet);
6. walk in that order and use only block-N getUserAccountData to determine if
   the pair has debt at N;
7. select the first 16 debt-bearing pairs.

No health-factor magnitude, collateral asset, debt size, oracle move or market
outcome enters cohort selection.

## Scientific calls

For every selected pair, every onchain scientific read MUST use the same block N:
- reserve configuration;
- user reserve status;
- supplied assets;
- user position/dynamic config;
- premium debt;
- Hub drawn index;
- Oracle reserve price;
- official getUserAccountData.

Reconstruct HF exactly as in the passing one-borrower block-pin fixture.

## PASS

MULTI_BORROWER_BLOCK_PIN_PASS only if:
- exactly 16 debt-bearing pairs selected;
- 16/16 reconstruct within unchanged relative error <=5e-5;
- all use identical block number/hash;
- zero latest/current fallback;
- zero unresolved read/reconstruction error.

Raw wallet addresses must not be persisted.

Passing proves same-block reconstruction can scale across multiple positions.
It does NOT authorize a liquidation shock curve or any price/liquidation outcome.
