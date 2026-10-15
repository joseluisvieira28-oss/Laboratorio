# PENDLE-PT-MATURITY-CONVERGENCE-001 — SOURCE / MECHANISM FREEZE V0.1

Status: FROZEN_SOURCE_FIRST / OUTCOMES LOCKED
Primary family: RV
Secondary family: CARRY

## Mechanism

Pendle Principal Token (PT) represents principal separated from future yield. At maturity PT becomes redeemable for its accounting asset; the YT claim expires.

Frozen research primitive:
**explicit tokenized-principal redemption anchor with fixed maturity**.

This is materially distinct from generic perpetual funding and from a standard futures basis contract. The asset itself contains a maturity redemption right.

## Who pays / acts

- PT buyers accept current discount in exchange for fixed-yield convergence;
- YT holders own the separated yield claim until expiry;
- arbitrage/liquidity providers connect PT market price to the maturity redemption anchor.

## Source authority

Official documentation:
- https://docs.pendle.finance/pendle-v2/ProtocolMechanics/YieldTokenization/PT
- https://api-v2.pendle.finance/core/docs
- https://docs.pendle.finance/pendle-v2-dev/Backend/ApiOverview

Public endpoints:
- GET https://api-v2.pendle.finance/core/v2/markets/all
- GET https://api-v2.pendle.finance/core/v3/{chainId}/markets/{address}/historical-data

## Source Gate only

Required PASS:
- public market enumeration works without credentials;
- market identity includes chain/address/expiry and PT/accounting-asset references sufficient to freeze an immutable population;
- historical endpoint returns timestamped market state;
- historical coverage can be measured before outcomes;
- source payloads can be hashed/preserved.

No convergence statistic, return, entry rule, holding period, fee model or PnL is authorized.

## Anti-selection

The eventual market population must be frozen by objective rules before any economic outcome is computed.
No "best PT", best chain, best maturity or best yield asset may be selected after viewing convergence performance.

## Failure classes

SOURCE_PASS
SOURCE_PARTIAL
SOURCE_BLOCKED
PROVENANCE_FAILURE
INSUFFICIENT_MARKET_POPULATION

NO_EDGE is impossible at this stage.
