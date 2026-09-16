# DEFI-LIQUIDATION-SHOCK-001 — SOURCE DATA GATE RECEIPT V0.2

## Classification

**SOURCE_DATA_INSUFFICIENT / CORPUS_DOMAIN_MISMATCH**

This supersedes the provisional V0.1 source-access classification after a direct Drive-root inventory surfaced the recent ZIPs. The mechanism is NOT classified NO_EDGE. No economic outcome was opened.

## What was actually inspected

The Drive root contains `MSEL_PILOT_DATA_15SEP2026.zip` (1,523,069,251 bytes). The current connector cannot stream files above 256 MiB, so the container itself could not be fully materialized.

However, separately exposed constituent archives from the same MSEL source workflow were downloaded and inspected by content:

- `raw_signature_pages.zip`
  - SHA-256: `3f410d236b8b92c63d4f103ae63c790da93aa040858df0bb725513dfe014aebe`
  - 25 JSON signature pages
  - 2,958 rows, 2,953 unique signatures
  - block-time span in the pages: 2025-06-13 12:22:17 UTC to 2026-08-13 13:38:17 UTC
  - 460 rows contain transaction errors
- `future_signature_index_v13.zip`
  - SHA-256: `c637e72d28a713851d57f846d1a10f76c1f0c1855bf1010f36264eb6311dce2e`
  - internal manifest artifact: `MSEL_PILOT25_OUTCOME_SOURCE_V13`
  - 25 target mints, 904 unique future signatures
  - source route: `getSignaturesForAddress(target_mint, until=frozen_create_signature)`
  - labels/returns/verdict explicitly not computed in the manifest
- `tx_000357_3vYxz5ZX4WNH.zip`
  - SHA-256: `138bfa77e305e362df0b5bc493cd13d4e7e2187b6d5c40045b712c2032683e1d`
- `tx_000510_4oE9bxaC3Fx6.zip`
  - SHA-256: `a9b3e44f6fdee0c5be5f8d3d01e10fc0f4c7514dcdfc85323cb1de41ab5956ab`

The two full-transaction ZIPs contain 939 file entries with 35 duplicates across the archives, yielding exactly 904 unique signatures. Their block-time span is 2025-06-13 12:28:07 UTC to 2025-06-14 11:48:53 UTC. 872 are successful and 32 failed.

## Content classification

The full transaction corpus was scanned using transaction account keys, invoked program IDs and log messages.

Unique transactions touching the candidate DeFi programs:
- marginfi v2 `MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA`: **0 / 904**
- Kamino Lend current program `KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD`: **0 / 904**
- Drift V2 `dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH`: **0 / 904**
- Save/Solend `So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo`: **0 / 904**

Unique transactions touching Pump.fun program `6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P`: **896 / 904**.

Log-message scan for `liquidat`, `borrow`, `repay`, `marginfi`, `kamino`, `solend`, or `drift`: **0 / 904**.

The internal index is explicitly keyed by 25 target token mints, and 24 of 25 target mint strings use the `pump` suffix.

Therefore the available raw is a Pump.fun/memecoin forensic source corpus, not a protocol-wide DeFi lending/perps liquidation corpus.

## Scientific meaning

This is **not evidence that DeFi liquidations lack an edge**. It is evidence that the uploaded Helius corpus cannot answer this lab's source question.

A sample gate cannot be frozen from this corpus because the number of valid DeFi liquidation events is not a meaningful population estimate; the corpus was selected for a different mechanism.

## Source-route feasibility remains open

External official documentation supports a viable future acquisition route:
- Helius archival Solana transaction/block history;
- explicit liquidation instructions/flows in major Solana lending/perps protocols;
- program-address filtering plus historical IDL/version pinning.

That route requires a new historical protocol-targeted raw acquisition or an already-existing DeFi corpus. It must be frozen before outcomes and cannot be rescued with outcome-driven protocol/size choices.

## Outcome firewall

- 2025/2026 price outcomes opened: FALSE
- returns computed: FALSE
- PnL computed: FALSE
- direction tested: FALSE
- protocol selected from outcomes: FALSE
- liquidation-size threshold selected from outcomes: FALSE
- live trading: FALSE
- exchange mutation: FALSE
- merge to main: FALSE

## Decision

**SOURCE_DATA_INSUFFICIENT / CORPUS_DOMAIN_MISMATCH**

Do not create FINAL PRE-DISCOVERY AUTHORITY and do not run Discovery from this corpus.

The next scientifically valid transition is a protocol-targeted DeFi liquidation source acquisition/reconstruction, then an outcome-blind liquidation-event census, then a prospectively frozen sample gate.
