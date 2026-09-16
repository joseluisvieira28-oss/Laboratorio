# DEFI-LIQUIDATION-SHOCK-001 — SOURCE ROUTE FEASIBILITY V0.1

Date: 2026-09-16
Status: SOURCE ROUTE DESIGNED / EXECUTION CREDENTIAL NOT EXPOSED / OUTCOMES LOCKED

## Current result

The uploaded MSEL/Helius raw cannot answer the DeFi liquidation question because it is a Pump.fun-targeted forensic corpus. A replacement protocol-targeted historical acquisition is therefore required.

## Preferred route — no paid data required by design

Current Helius material and current public documentation support the following distinction:

- standard Solana archival methods are available through the Helius archival system on free and paid plans;
- the Free plan currently advertises 1M credits and 10 requests/second;
- Helius-only `getTransactionsForAddress` is the faster time-filtered path but is available on paid plans and costs 100 credits/call;
- the older standard pattern `getSignaturesForAddress` + `getTransaction` remains a valid archival backfill mechanism, though it can be expensive/slow at scale.

Therefore V0.1 deliberately implements only standard read-only RPC calls and does not require purchase of a paid Helius plan.

## Collector committed

`source/collect_protocol_history_v0_1.py`

Frozen source window:
- 2021-01-01T00:00:00Z
- 2024-12-31T23:59:59Z

Frozen candidate protocol families:
- Save / Solend
- marginfi v2
- Kamino Lend
- Drift v2

The collector:
- pages program-address signature history;
- skips full-transaction fetches outside the frozen source window;
- fetches historical full transactions inside the window;
- preserves exact JSON-RPC response bytes + SHA-256 receipts;
- extracts direct and inner/CPI instructions invoking the target protocol;
- records current/reference liquidation discriminator matches only as non-authoritative hints;
- queries no market prices;
- computes no returns, PnL, direction, execution metrics or edge verdict.

Any safety page cap makes a run explicitly PARTIAL and unable to establish `SOURCE_DATA_PASS`.

## Decoder evidence already pinned as references

Save / Solend:
- production program: `So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo`
- public pinned SDK enum contains liquidation instruction tags 12 and 17;
- tag 17 is the documented `LiquidateObligationAndRedeemReserveCollateral` path.

marginfi v2:
- mainnet program: `MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA`
- historical/public IDL reference for `lending_account_liquidate`: discriminator `d6a997d5fba756db`.

Kamino Lend:
- mainnet program: `KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD`
- current generated SDK reference for `liquidateObligationAndRedeemReserveCollateral`: discriminator `b1479acce2854a37`.

Drift v2:
- program: `dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH`
- current/reference `liquidate_perp` discriminator identified, but Drift has several liquidation families; it is not a complete decoder freeze.

All remain `REFERENCE_ONLY` until historical program/IDL applicability is proven over the relevant dates.

## Current blocker

The connected research runtime does not currently expose a Helius/API archival RPC credential or URL, so the collector cannot execute the historical census in this session.

This is not a paid-data blocker: a free archival RPC credential is sufficient to attempt V0.1. It is an execution-environment credential dependency.

If a free-tier route later hits an explicit credit/rate/completeness barrier, classify the acquisition accordingly and stop. Do not silently upgrade or purchase data.

## Secondary routes

Public Dune queries clearly exist for historical Solana liquidations (including Solend, marginfi, Kamino and Drift). They may reduce discovery cost by serving as a candidate-signature index, but they are not raw authority and no connected Dune API is available in this session.

Flipside curated liquidation tables may likewise be useful as a reconciliation layer, but enriched fields such as USD values must not replace raw event-time evidence. Any paid/trial/billable route requires user authorization first.

## Scientific state transition

Current lab state remains:

`SOURCE_DATA_INSUFFICIENT / CORPUS_DOMAIN_MISMATCH`

The route to promotion is:

raw protocol history acquisition
→ historical decoder/version proof
→ deterministic liquidation event census
→ completeness + field-coverage audit
→ freeze numerical sample gate + clustering
→ SOURCE_DATA_PASS (only if justified)
→ FINAL PRE-DISCOVERY AUTHORITY
→ one Discovery

No economic outcome has been opened.
